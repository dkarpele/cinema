from datetime import datetime

from aiokafka import AIOKafkaProducer
from ssl import SSLContext

from core.config import kafka_settings


class Kafka:
    def __init__(self, topic: str):
        self.topic = topic
        context = SSLContext()
        context.load_verify_locations(cafile=kafka_settings.ssl_cafile)
        self.producer = AIOKafkaProducer(
            bootstrap_servers=kafka_settings.bootstrap_servers.split(),
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=kafka_settings.user,
            sasl_plain_password=kafka_settings.password,
            ssl_context=context
        )

    async def produce_viewed_frame(self,
                                   user_id: str,
                                   movie_id: str,
                                   begin_time: datetime,
                                   end_time: datetime):
        await self.producer.start()
        try:
            await self.producer.send_and_wait(
                topic=self.topic,
                key='%'.join([str(user_id), str(movie_id)]).encode('utf-8'),
                value='%'.join([str(begin_time), str(end_time)]).
                encode('utf-8')
            )
        finally:
            await self.producer.stop()


async def get_kafka():
    yield Kafka(kafka_settings.topic)
