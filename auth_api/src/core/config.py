import os
from logging import config as logging_config
from pydantic import BaseSettings, Field

from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class MainConf(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


class Settings(MainConf):
    project_name: str = Field(..., env='PROJECT_NAME')
    redis_host: str = Field(..., env='REDIS_HOST')
    redis_port: int = Field(..., env='REDIS_PORT')
    host: str = Field(..., env='HOST_AUTH')
    port: int = Field(..., env='PORT_AUTH')
    secret_key: str = Field(..., env='SECRET_KEY')
    secret_key_refresh: str = Field(..., env='SECRET_KEY_REFRESH')


settings = Settings()


class DBCreds(MainConf):
    dbname: str = Field(..., env="DB_NAME")
    user: str = Field(..., env="DB_USER")
    password: str = Field(..., env="DB_PASSWORD")
    host: str = Field(env="DB_HOST", default='127.0.0.1')
    port: int = Field(env="DB_PORT", default=5432)
    options: str = '-c search_path=%s' % os.environ.get('PG_SCHEMA')


database_dsn = DBCreds()


class YandexCreds(MainConf):
    client_id: str = Field(..., env='YA_CLIENT_ID')
    secret: str = Field(..., env='YA_SECRET')


yandex_config = YandexCreds()


class GoogleCreds(MainConf):
    client_id: str = Field(..., env='GOOGLE_CLIENT_ID')
    secret: str = Field(..., env='GOOGLE_SECRET')


google_config = GoogleCreds()


class JaegerCreds(MainConf):
    start: str = Field(..., env='JAEGER_START')
    agent_host_name: str = Field(..., env='JAEGER_AGENT_HOST_NAME')
    agent_port: str = Field(..., env='JAEGER_AGENT_PORT')


jaeger_config = JaegerCreds()


class RateLimit(MainConf):
    request_limit_per_minute: int = Field(env="REQUEST_LIMIT_PER_MINUTE",
                                          default=20)
    is_rate_limit: bool = (os.getenv('IS_RATE_LIMIT', 'False') == 'True')


rl = RateLimit()

LOGIN_DESC = "user's login"
FIRST_NAME_DESC = "user's first name"
LAST_NAME_DESC = "user's last name"
PASSWORD_DESC = "Password: Minimum eight characters, " \
                "at least one letter and one number:"
ROLE_TITLE_DESC = "Roles title"
PERMISSIONS_DESC = "Permission for the role"
PAGE_DESC = "Номер страницы"
SIZE_DESC = "Количество элементов на странице"
