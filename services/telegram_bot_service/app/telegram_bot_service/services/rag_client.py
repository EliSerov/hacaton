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

        self._reply_queue = "amq.rabbitmq.reply-to"
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
        if self._consumer_started:
            return
        assert self._channel is not None

        async def on_response(message: aio_pika.IncomingMessage) -> None:
            cid = message.correlation_id
            if not cid:
                return
            async with self._pending_lock:
                fut = self._pending.pop(cid, None)
            if fut is None or fut.done():
                return
            try:
                data = json.loads(message.body.decode("utf-8"))
            except Exception:
                data = {"summary": "Некорректный ответ от RAG-сервиса.", "articles": []}
            fut.set_result(data)

        await self._channel.consume(on_response, queue_name=self._reply_queue, no_ack=True)
        self._consumer_started = True

    async def close(self) -> None:
        # Fail any pending futures
        async with self._pending_lock:
            for cid, fut in list(self._pending.items()):
                if not fut.done():
                    fut.set_exception(RuntimeError("RAGClient is closing"))
            self._pending.clear()

        try:
            if self._channel and not self._channel.is_closed:
                await self._channel.close()
        finally:
            if self._conn and not self._conn.is_closed:
                await self._conn.close()

        self._conn = None
        self._channel = None
        self._exchange = None
        self._consumer_started = False
        logger.info("RAGClient closed")

    async def _rpc_call(self, routing_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._conn or not self._channel or not self._exchange:
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
            reply_to=self._reply_queue,
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
                self._pending.pop(correlation_id, None)
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
