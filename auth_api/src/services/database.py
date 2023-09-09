import datetime

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import rl
from db.redis import Redis, get_redis, AbstractCache
from db.postgres import get_session
from services.exceptions import too_many_requests
from services.backoff import backoff


@lru_cache()
def get_cache_service(
        redis: Redis = Depends(get_redis)) -> AbstractCache:
    return redis


@lru_cache()
def get_db_service(
        db: AsyncSession = Depends(get_session)) -> AsyncSession:
    return db


DbDep = Annotated[AsyncSession, Depends(get_db_service)]
CacheDep = Annotated[AbstractCache, Depends(get_cache_service)]


@backoff(service='Redis')
async def rate_limit(request: Request,
                     cache: CacheDep):
    """
    Ограничение количества запросов к серверу (Rate limit).
    Используется алгоритм Leaky bucket. Запросы, которые не прошли лимит,
    получат HTTP-статус 429 Too Many Requests.
    :param request: Из request получим хост:порт юзера
    :param cache: redis cache
    :return:
    """
    if not rl.is_rate_limit:
        return
    pipe = await cache.create_pipeline()
    now = datetime.datetime.now()
    host = str(request.client)
    key = f'{host}:{now.minute}'
    pipe.incr(key, 1)
    pipe.expire(key, 59)
    result = await pipe.execute()
    request_number = result[0]
    if request_number > rl.request_limit_per_minute:
        raise too_many_requests
