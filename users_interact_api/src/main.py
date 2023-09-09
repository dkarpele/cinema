import logging
import os

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1 import views, bookmarks, likes, reviews
from core.config import settings, mongo_settings
from core.logger import LOGGING
from core.logger_wo_logstash import LOGGING as LOGGING_WO_LOGSTASH
from db import mongo

sentry_sdk.init(integrations=[FastApiIntegration()])

logstash = (os.getenv('LOGSTASH_ENABLE', 'False') == 'True')
log = LOGGING if logstash else LOGGING_WO_LOGSTASH


async def startup():
    if mongo_settings.user and mongo_settings.password:
        mongo.mongo = mongo.Mongo(
            f'mongodb://'
            f'{mongo_settings.user}:{mongo_settings.password}@'
            f'{mongo_settings.host}:{mongo_settings.port}'
        )
    else:
        mongo.mongo = mongo.Mongo(
            f'mongodb://'
            f'{mongo_settings.host}:{mongo_settings.port}'
        )


async def shutdown():
    pass


@asynccontextmanager  # type: ignore[arg-type]
async def lifespan(app: FastAPI):
    await startup()
    yield


app = FastAPI(
    title="Api to analyze users behaviour",
    description="Api to analyze users behaviour",
    version="1.0.0",
    docs_url='/api/openapi-user-analyze',
    openapi_url='/api/openapi-user-analyze.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan,)


app.include_router(views.router,
                   prefix='/api/v1/views',
                   tags=['views'])
app.include_router(bookmarks.router,
                   prefix='/api/v1/bookmarks',
                   tags=['bookmarks'])
app.include_router(likes.router,
                   prefix='/api/v1/likes',
                   tags=['likes'])
app.include_router(reviews.router,
                   prefix='/api/v1/reviews',
                   tags=['reviews'])

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=f'{settings.host}',
        port=settings.port,
        log_config=log,
        log_level=logging.DEBUG,
    )
