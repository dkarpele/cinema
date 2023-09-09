from kafka import KafkaConsumer

from core.config import kafka_settings

consumer = KafkaConsumer(
            kafka_settings.topic,
            bootstrap_servers=kafka_settings.bootstrap_servers,
            auto_offset_reset='earliest',
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=kafka_settings.user,
            sasl_plain_password=kafka_settings.password,
            ssl_cafile=kafka_settings.ssl_cafile,

            )


# admin_client = KafkaAdminClient(
#             bootstrap_servers=kafka_settings.bootstrap_servers,
#             security_protocol="SASL_SSL",
#             sasl_mechanism="SCRAM-SHA-512",
#             sasl_plain_username=kafka_settings.user,
#             sasl_plain_password=kafka_settings.password,
#             ssl_cafile=kafka_settings.ssl_cafile,
#             )
# admin_client.delete_topics('views')

print("ready")
i = 0
# consumer.subscribe(['views'])
for msg in consumer:
    print(msg)
    i = i + 1
    print(i)

print('after for')
