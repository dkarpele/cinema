import logging

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1 import films, genres, persons
from core.config import settings
from core.logger import LOGGING
from db import elastic, redis


async def startup():
    redis.redis = redis.Redis(host=settings.redis_host,
                              port=settings.redis_port,
                              ssl=False)
    elastic.es = elastic.Elastic(
        hosts=[f'{settings.elastic_host}:{settings.elastic_port}'])


async def shutdown():
    await redis.redis.close()
    await elastic.es.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()

app = FastAPI(
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=settings.project_name,
    description="Информация о фильмах, жанрах и людях, участвовавших в "
                "создании произведения",
    version="1.0.0",
    # Адрес документации в красивом интерфейсе
    docs_url='/api/openapi-content',
    # Адрес документации в формате OpenAPI
    openapi_url='/api/openapi-content.json',
    # Можно сразу сделать небольшую оптимизацию сервиса
    # и заменить стандартный JSON-сереализатор на более шуструю версию,
    # написанную на Rust
    default_response_class=ORJSONResponse,
    lifespan=lifespan)


# Подключаем роутер к серверу, указав префикс /v1/films
# Теги указываем для удобства навигации по документации
app.include_router(films.router, prefix='/api/v1/films', tags=['films'])
app.include_router(genres.router, prefix='/api/v1/genres', tags=['genres'])
app.include_router(persons.router, prefix='/api/v1/persons', tags=['persons'])


if __name__ == '__main__':
    # Приложение может запускаться командой
    # `uvicorn main:app --host 0.0.0.0 --port 8000`
    # но чтобы не терять возможность использовать дебагер,
    # запустим uvicorn сервер через python
    uvicorn.run(
        'main:app',
        host=f'{settings.host}',
        port=settings.port,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
