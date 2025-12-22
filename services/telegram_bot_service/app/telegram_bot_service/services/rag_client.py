from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Optional, List

import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

from telegram_bot_service.settings import settings
from telegram_bot_service.models.contracts import (
    SearchRequest,
    SearchResponse,
    RecommendRequest,
    QuizRequest,
)

logger = logging.getLogger(__name__)


class RAGClient:
    """RabbitMQ RPC client for the RAG service (Direct Reply-to).

    - Keeps a single robust connection + channel
    - Starts exactly one consumer for `amq.rabbitmq.reply-to`
    - Supports concurrent in-flight RPC calls via correlation_id map
    """

    def __init__(self) -> None:
        self._conn: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractRobustChannel] = None
        self._exchange: Optional[aio_pika.Exchange] = None

        self._reply_queue: Optional[str] = None
        self._reply_q: Optional[aio_pika.Queue] = None
        self._pending: Dict[str, asyncio.Future[Dict[str, Any]]] = {}
        self._pending_lock = asyncio.Lock()
        self._consumer_started = False

    async def connect(self) -> None:
        if self._conn:
            return

        self._conn = await aio_pika.connect_robust(settings.amqp_url)
        self._channel = await self._conn.channel()
        await self._channel.set_qos(prefetch_count=20)

        self._exchange = await self._channel.declare_exchange(
            settings.rag_exchange, aio_pika.ExchangeType.DIRECT, durable=True
        )

        await self._start_reply_consumer()
        logger.info("RAGClient connected. Exchange='%s'", settings.rag_exchange)

    async def _start_reply_consumer(self) -> None:
        """
        Start a private reply queue consumer for RPC responses.

        We intentionally avoid RabbitMQ "direct reply-to" (amq.rabbitmq.reply-to) here because
        it can break on reconnects/consumer cancellations and causes:
        PRECONDITION_FAILED - fast reply consumer does not exist
        """
        if self._consumer_started:
            return
        assert self._channel is not None

        # Server-named, exclusive, auto-delete queue: stable for the lifetime of this connection.
        # RobustChannel will re-declare it on reconnect.
        self._reply_q = await self._channel.declare_queue(
            name="",
            durable=False,
            exclusive=True,
            auto_delete=True,
        )
        self._reply_queue = self._reply_q.name

        async def on_response(message: aio_pika.IncomingMessage) -> None:
            cid = message.correlation_id
            if not cid:
                return
            try:
                payload = json.loads(message.body.decode("utf-8"))
            except Exception:
                logger.exception("Failed to decode RPC response JSON")
                return

            async with self._pending_lock:
                fut = self._pending.pop(cid, None)

            if fut and not fut.done():
                fut.set_result(payload)

        await self._reply_q.consume(on_response, no_ack=True)
        self._consumer_started = True


    async def _rpc_call(self, routing_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._conn or not self._channel or not self._exchange or not self._reply_queue:
            raise RuntimeError("RAGClient is not connected. Call connect() on startup.")

        correlation_id = str(uuid.uuid4())
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        headers = {}
        if settings.service_api_key:
            headers["x-api-key"] = settings.service_api_key

        fut: asyncio.Future[Dict[str, Any]] = asyncio.get_running_loop().create_future()
        async with self._pending_lock:
            self._pending[correlation_id] = fut

        msg = aio_pika.Message(
            body=body,
            reply_to=self._reply_queue or "",
            correlation_id=correlation_id,
            headers=headers,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await self._exchange.publish(msg, routing_key=routing_key)

        try:
            return await asyncio.wait_for(fut, timeout=settings.rag_rpc_timeout_s)
        except Exception:
            async with self._pending_lock:
                await self._pending.pop(correlation_id, None)
            raise

    async def search(
        self,
        query: str,
        author: Optional[str] = None,
        date: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> SearchResponse:
        req = SearchRequest(query=query.strip(), filters={"author": author, "date": date, "topic": topic})
        raw = await self._rpc_call(settings.rag_routing_search, req.model_dump(exclude_none=True))
        return SearchResponse.model_validate(raw)

    async def recommend(self, seed_url: str, top_k: int = 5) -> SearchResponse:
        req = RecommendRequest(url=seed_url, top_k=top_k)
        raw = await self._rpc_call(settings.rag_routing_recommend, req.model_dump())
        return SearchResponse.model_validate(raw)

    async def quiz(self, urls: List[str], n_questions: int = 8) -> SearchResponse:
        req = QuizRequest(urls=urls, n_questions=n_questions)
        raw = await self._rpc_call(settings.rag_routing_quiz, req.model_dump())
        return SearchResponse.model_validate(raw)


_rag_client: Optional[RAGClient] = None


def set_rag_client(client: RAGClient) -> None:
    global _rag_client
    _rag_client = client


def get_rag_client() -> RAGClient:
    if _rag_client is None:
        raise RuntimeError("RAG client is not initialized")
    return _rag_client