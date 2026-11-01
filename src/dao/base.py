from typing import Any, Generic, TypeVar, Type, Optional, Dict

from sqlalchemy import select, func

from dependencies.db import DBDependency
from models.base import Base

T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    model: Type[T]

    def __init__(self, db: DBDependency):
        self.db = db

    def _model_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Расширенная рекурсивная конвертация модели в словарь.
        Автоматически обрабатывает загруженные связи (relationships).
        """
        if obj is None:
            return {}

        result = {
            column.key: getattr(obj, column.key) for column in obj.__table__.columns
        }

        # Рекурсивно подтягиваем связи, которые загружены в сессии
        from sqlalchemy.orm import attributes

        for key, relationship in obj.__mapper__.relationships.items():
            if key in attributes.instance_state(obj).unloaded:
                continue
            value = getattr(obj, key)
            if value is None:
                result[key] = None
            elif isinstance(value, list):
                result[key] = [self._model_to_dict(item) for item in value]
            else:
                result[key] = self._model_to_dict(value)

        return result

    async def count(self) -> int:
        async with self.db.read_only_scope() as session:
            result = await session.execute(select(func.count()).select_from(self.model))
            return result.scalar_one()

    async def create(self, **kwargs: Any) -> Dict[str, Any]:
        async with self.db.session_scope() as session:
            obj = self.model(**kwargs)
            session.add(obj)
            await session.flush()
            await session.refresh(obj)
            return self._model_to_dict(obj)

    async def get_by_id(self, id) -> Optional[Type[T]]:
        async with self.db.session_scope() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()

    async def update(self, obj: T) -> Dict[str, Any]:
        async with self.db.session_scope() as session:
            merged = await session.merge(obj)
            await session.flush()
            await session.refresh(merged)
            return self._model_to_dict(merged)

    async def delete(self, obj: T) -> None:
        async with self.db.session_scope() as session:
            await session.delete(obj)

    # async def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    #     """Получение всех — возвращает список словарей"""
    #     async with self.db.read_only_scope() as session:
    #         result = await session.execute(
    #             select(self.model)
    #             .limit(limit)
    #             .offset(offset)
    #             # .order_by(self.model.id.desc())
    #         )
    #         objects = result.scalars().all()
    #         return [self._model_to_dict(obj) for obj in objects]
