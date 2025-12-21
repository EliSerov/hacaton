import json
import logging
from typing import Awaitable, Callable, Dict, Optional

import aio_pika
from aio_pika.abc import AbstractRobustConnection


logger = logging.getLogger(__name__)


class RpcServer:
    def __init__(
        self,
        conn: AbstractRobustConnection,
        exchange_name: str,
        queue_name: str,
        routing_key: str,
        handler: Callable[[dict, dict], Awaitable[dict]],
        prefetch_count: int = 1,
        required_api_key: Optional[str] = None,
    ) -> None:
        self._conn = conn
        self._exchange_name = exchange_name
        self._queue_name = queue_name
        self._routing_key = routing_key
        self._handler = handler
        self._prefetch_count = prefetch_count
        self._required_api_key = required_api_key

    async def start(self) -> None:
        channel = await self._conn.channel()
        await channel.set_qos(prefetch_count=self._prefetch_count)

        exchange = await channel.declare_exchange(self._exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue(self._queue_name, durable=True)
        await queue.bind(exchange, routing_key=self._routing_key)

        async def on_message(message: aio_pika.IncomingMessage) -> None:
            trace_id = (message.headers or {}).get("x-trace-id", "")
            log_extra = {"trace_id": trace_id}

            try:
                if not message.reply_to or not message.correlation_id:
                    logger.warning("RPC message missing reply_to/correlation_id", extra=log_extra)
                    await message.ack()
                    return

                if self._required_api_key:
                    api_key = (message.headers or {}).get("x-api-key")
                    if api_key != self._required_api_key:
                        logger.warning("Unauthorized RPC call", extra=log_extra)
                        body = json.dumps({"summary": "Unauthorized", "articles": []}, ensure_ascii=False).encode("utf-8")
                        await channel.default_exchange.publish(
                            aio_pika.Message(body=body, correlation_id=message.correlation_id),
                            routing_key=message.reply_to,
                        )
                        await message.ack()
                        return

                payload = json.loads(message.body.decode("utf-8"))
                result = await self._handler(payload, {"trace_id": trace_id})
                body = json.dumps(result, ensure_ascii=False).encode("utf-8")
                await channel.default_exchange.publish(
                    aio_pika.Message(body=body, correlation_id=message.correlation_id),
                    routing_key=message.reply_to,
                )
                await message.ack()
            except Exception as e:
                logger.exception("RPC handler failed", extra=log_extra)
                try:
                    body = json.dumps({"summary": f"Ошибка обработки запроса: {e}", "articles": []}, ensure_ascii=False).encode("utf-8")
                    if message.reply_to and message.correlation_id:
                        await channel.default_exchange.publish(
                            aio_pika.Message(body=body, correlation_id=message.correlation_id),
                            routing_key=message.reply_to,
                        )
                finally:
                    await message.ack()

        await queue.consume(on_message)
        logger.info("RPC server started", extra={"trace_id": ""})
