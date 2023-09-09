from logging import config as logging_config

from dotenv import load_dotenv
from pydantic import Field

from core.logger import LOGGING, MainConf

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
load_dotenv()


class Settings(MainConf):
    host: str = Field(..., env='HOST_USERS_ANALYZE')
    port: int = Field(..., env='PORT_USERS_ANALYZE')
    host_auth: str = Field(..., env='HOST_AUTH')
    port_auth: int = Field(..., env='PORT_AUTH')
    host_content: str = Field(..., env='HOST_CONTENT')
    port_content: int = Field(..., env='PORT_CONTENT')


settings = Settings()


class KafkaCreds(MainConf):
    user: str = Field(..., env="KAFKA_USER")
    password: str = Field(..., env="KAFKA_PASSWORD")
    topic: str = Field(..., env='TOPIC')
    bootstrap_servers: str = Field(..., env='KAFKA_SERVERS')
    ssl_cafile: str = Field(..., env='KAFKA_CAFILE')


kafka_settings = KafkaCreds()


class MongoCreds(MainConf):
    host: str = Field(..., env="MONGO_HOST")
    port: str = Field(..., env="MONGO_PORT")
    user: str = Field(default=None, env="MONGO_INITDB_ROOT_USERNAME")
    password: str = Field(default=None, env="MONGO_INITDB_ROOT_PASSWORD")
    db: str = Field(..., env="MONGO_INITDB_DATABASE")


mongo_settings = MongoCreds()
