import aio_pika
from aio_pika.abc import AbstractRobustConnection


async def connect(amqp_url: str) -> AbstractRobustConnection:
    return await aio_pika.connect_robust(amqp_url)
