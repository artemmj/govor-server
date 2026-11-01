import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError

from settings import settings

logger = logging.getLogger(__name__)


class DBDependency:
    def __init__(self) -> None:
        self._engine = create_async_engine(
            url=settings.db_settings.db_url,
            echo=settings.db_settings.db_echo,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,  # Проверка соединения перед использованием
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,  # Ручное управление flush
            autocommit=False,
        )

    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            yield session

    @asynccontextmanager
    async def session_scope(
        self,
        *,
        read_only: bool = False,
        isolation_level: Optional[str] = None,
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Контекстный менеджер с гарантированным commit/rollback.

        Args:
            read_only: Если True, коммит не выполняется (только чтение)
            isolation_level: Уровень изоляции для этой транзакции
        """
        session = self._session_factory()

        if isolation_level:
            await session.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")

        try:
            yield session

            if not read_only:
                await session.commit()
            else:
                await session.rollback()

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database transaction failed: %s", str(e))
            raise

        except Exception as e:
            await session.rollback()
            logger.error("Unexpected error in transaction: %s", str(e))
            raise

        finally:
            await session.close()

    @asynccontextmanager
    async def read_only_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Ярлык для сессий только на чтение"""
        async with self.session_scope(read_only=True) as session:
            yield session

    @asynccontextmanager
    async def nested_transaction(
        self, session: AsyncSession
    ) -> AsyncGenerator[None, None]:
        """Создаёт savepoint внутри существующей транзакции"""
        try:
            await session.begin_nested()
            yield
        except Exception:
            await session.rollback()
            raise

    async def close(self) -> None:
        """Graceful shutdown - закрывает пул соединений"""
        await self._engine.dispose()


# Синглтон на всё приложение: engine и пул соединений создаются
# один раз при старте процесса, а не на каждый запрос
db_dependency = DBDependency()
