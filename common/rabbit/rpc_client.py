import asyncio
import json
import uuid
from typing import Any, Dict, Optional

import aio_pika
from aio_pika.abc import AbstractRobustConnection


class RpcClient:
    def __init__(self, conn: AbstractRobustConnection, exchange_name: str, api_key: str) -> None:
        self._conn = conn
        self._exchange_name = exchange_name
        self._api_key = api_key

    async def call(
        self,
        routing_key: str,
        payload: Dict[str, Any],
        timeout_s: float = 120.0,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        channel = await self._conn.channel()
        exchange = await channel.declare_exchange(self._exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)

        callback_queue = "amq.rabbitmq.reply-to"
        correlation_id = str(uuid.uuid4())
        fut: asyncio.Future[Dict[str, Any]] = asyncio.get_running_loop().create_future()

        async def on_response(message: aio_pika.IncomingMessage) -> None:
            if message.correlation_id == correlation_id and not fut.done():
                data = json.loads(message.body.decode("utf-8"))
                fut.set_result(data)

        await channel.consume(on_response, queue_name=callback_queue, no_ack=True)

        headers = {"x-api-key": self._api_key}
        if trace_id:
            headers["x-trace-id"] = trace_id

        msg = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            reply_to=callback_queue,
            correlation_id=correlation_id,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers=headers,
        )
        await exchange.publish(msg, routing_key=routing_key)

        return await asyncio.wait_for(fut, timeout=timeout_s)
