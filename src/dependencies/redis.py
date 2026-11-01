from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis
import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool

from settings import settings


class RedisDependency:
    def __init__(self) -> None:
        self._url = settings.redis_settings.redis_url
        self._async_pool: ConnectionPool = self._init_async_pool()
        self._sync_pool: ConnectionPool = self._init_sync_pool()

    def _init_async_pool(self) -> ConnectionPool:
        return ConnectionPool.from_url(
            url=self._url, encoding="utf-8", decode_responses=True
        )

    def _init_sync_pool(self) -> ConnectionPool:
        sync_url = self._url.replace(
            "redis://", "redis://"
        )  # URL одинаковый, но используется sync-клиент
        return redis.ConnectionPool.from_url(
            url=sync_url, encoding="utf-8", decode_responses=True
        )

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[aioredis.Redis, None]:
        """Асинхронный клиент для FastAPI (WebSocket, кэш)"""
        redis_client = aioredis.Redis(connection_pool=self._async_pool)
        try:
            yield redis_client
        finally:
            await redis_client.aclose()

    def get_sync_client(self) -> redis.Redis:
        """Синхронный клиент для Celery задач"""
        return redis.Redis(connection_pool=self._sync_pool)


# Синглтон-инстанс для использования в зависимостях и Celery
redis_dependency = RedisDependency()
