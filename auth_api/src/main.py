import logging
import uuid
from contextlib import asynccontextmanager

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.middleware import is_valid_uuid4
from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import ORJSONResponse

from api.v1 import auth, oauth, users, roles, users_unauth
from core.config import settings, database_dsn, jaeger_config
from core.logger import LOGGING
from db import redis, postgres
from services.database import rate_limit
from services.token import check_access_token
from services.users import check_admin_user
from tracer import configure_tracer, configure_instrument


async def startup():
    redis.redis = redis.Redis(host=settings.redis_host,
                              port=settings.redis_port,
                              ssl=False)
    postgres.postgres = postgres.Postgres(
                      f'postgresql+asyncpg://'
                      f'{database_dsn.user}:{database_dsn.password}@'
                      f'{database_dsn.host}:{database_dsn.port}/'
                      f'{database_dsn.dbname}')
    postgres.get_session()


async def shutdown():
    await redis.redis.close()
    await postgres.postgres.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()


if jaeger_config.start == "True":
    configure_tracer()

app = FastAPI(
    title=settings.project_name,
    description="Api for users auth",
    version="1.0.0",
    docs_url='/api/openapi-auth',
    openapi_url='/api/openapi-auth.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    dependencies=[Depends(rate_limit)])

app.add_middleware(
    CorrelationIdMiddleware,
    header_name='X-Request-ID',
    update_request_header=True,
    generator=lambda: uuid.uuid4().hex,
    validator=is_valid_uuid4,
    transformer=lambda a: a,
)

if jaeger_config.start == "True":
    configure_instrument(app)


@app.middleware('http')
async def before_request(request: Request, call_next):
    response = await call_next(request)
    request_id = request.headers.get('X-Request-Id')
    if not request_id:
        return ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                              content={'detail': 'X-Request-Id is required'})
    return response


app.include_router(auth.router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(oauth.router, prefix='/api/v1/oauth', tags=['oauth'])
app.include_router(roles.router, prefix='/api/v1/roles', tags=['roles'],
                   dependencies=[Depends(check_access_token),
                                 Depends(check_admin_user)])
app.include_router(users.router, prefix='/api/v1/users', tags=['users'],
                   dependencies=[Depends(check_access_token)])
app.include_router(users_unauth.router, prefix='/api/v1/users_unauth',
                   tags=['users_unauth'],)

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=f'{settings.host}',
        port=settings.port,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
