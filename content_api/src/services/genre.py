from functools import lru_cache
from fastapi import Depends

from db.elastic import get_elastic, Elastic
from db.redis import get_redis, Redis
from models.genres import Genre
from services.service import IdRequestService, ListService


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: Elastic = Depends(get_elastic)) -> IdRequestService:
    return IdRequestService(redis, elastic, Genre)


@lru_cache()
def get_genre_list_service(
        redis: Redis = Depends(get_redis),
        elastic: Elastic = Depends(get_elastic)) -> ListService:
    return ListService(redis, elastic, Genre)
