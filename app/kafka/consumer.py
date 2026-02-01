import json
from aiokafka import AIOKafkaConsumer

from app.logging_config import logger
from app.settings import settings
from app.kafka.handlers import handle_payment_event, handle_refund_event


async def start_kafka_consumer() -> None:
    consumer = AIOKafkaConsumer(
        settings.kafka_payment_topic,
        settings.kafka_refund_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_group_id,
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    logger.info("Starting Kafka consumer for topics: %s, %s",
                settings.kafka_payment_topic, settings.kafka_refund_topic)

    await consumer.start()
    try:
        async for msg in consumer:
            logger.info("Received message from topic %s: %s", msg.topic, msg.value)
            try:
                if msg.topic == settings.kafka_payment_topic:
                    await handle_payment_event(msg.value)
                    logger.info("Processed payment event: %s", msg.value.get("id"))
                elif msg.topic == settings.kafka_refund_topic:
                    await handle_refund_event(msg.value)
                    logger.info("Processed refund event: %s", msg.value.get("id"))

                await consumer.commit()
                logger.debug("Committed offset for message: %s", msg.offset)
            except Exception as e:
                logger.exception(
                    "Failed to process message from topic %s, offset %s. Will retry.",
                    msg.topic, msg.offset
                )

    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped.")
