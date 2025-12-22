import asyncio
import logging
from typing import Optional

from common.config import AppSettings
from common.logging import setup_logging
from common.rabbit.connection import connect
from common.rabbit.rpc_server import RpcServer

from rag_service.embedder import QueryEmbedder
from rag_service.qdrant_repo import QdrantSearchRepository
from rag_service.retriever import Retriever
from rag_service.prompt_builder import PromptBuilder
from rag_service.llm import LlamaCppLLM
from rag_service.mapper import ContractMapper
from rag_service.service import RagService


logger = logging.getLogger(__name__)


async def main() -> None:
    settings = AppSettings()
    setup_logging(settings.log_level)

    conn = await connect(settings.amqp_url)

    # Heavy init (LLM load) can take a long time; start consumers immediately
    # so we don't accumulate unconsumed messages in RabbitMQ.
    rag_ready = asyncio.Event()
    rag_holder: dict = {"rag": None}  # type: ignore[var-annotated]

    async def init_rag() -> None:
        logger.info("Initializing RAG components (LLM warmup may take a while)", extra={"trace_id": ""})
        llm = LlamaCppLLM(
            model_path=settings.llm_model_path,
            n_ctx=settings.llm_n_ctx,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            top_p=settings.llm_top_p,
            n_gpu_layers=settings.llm_n_gpu_layers,
        )

        embedder = QueryEmbedder(settings.embed_model)
        qrepo = QdrantSearchRepository(settings.qdrant_host, settings.qdrant_port, settings.qdrant_collection)
        retriever = Retriever(qrepo)
        rag_holder["rag"] = RagService(
            embedder=embedder,
            qrepo=qrepo,
            retriever=retriever,
            llm=llm,
            prompt_builder=PromptBuilder(),
            mapper=ContractMapper(),
        )
        rag_ready.set()
        logger.info("RAG components initialized", extra={"trace_id": ""})

    # Ensure GPU/LLM single-threaded execution across queues
    gpu_lock = asyncio.Lock()

    async def get_rag() -> Optional[RagService]:
        if not rag_ready.is_set():
            # Do not block the queue indefinitely; reply with a clear message.
            return None
        return rag_holder["rag"]

    async def search_handler(payload: dict, meta: dict) -> dict:
        rag = await get_rag()
        if rag is None:
            return {"summary": "Сервис прогревается (загрузка модели). Попробуйте через 30–60 секунд.", "articles": []}
        async with gpu_lock:
            return rag.search(payload, trace_id=meta.get("trace_id", ""))

    async def recommend_handler(payload: dict, meta: dict) -> dict:
        rag = await get_rag()
        if rag is None:
            return {"summary": "Сервис прогревается (загрузка модели). Попробуйте позже.", "articles": []}
        async with gpu_lock:
            return rag.recommend(payload, trace_id=meta.get("trace_id", ""))

    async def quiz_handler(payload: dict, meta: dict) -> dict:
        rag = await get_rag()
        if rag is None:
            return {"summary": "Сервис прогревается (загрузка модели). Попробуйте позже.", "articles": []}
        async with gpu_lock:
            return rag.quiz(payload, trace_id=meta.get("trace_id", ""))

    servers = [
        RpcServer(conn, settings.rag_rpc_exchange, "rag.search.q", settings.rag_search_routing_key, search_handler, prefetch_count=1, required_api_key=settings.service_api_key),
        RpcServer(conn, settings.rag_rpc_exchange, "rag.recommend.q", settings.rag_recommend_routing_key, recommend_handler, prefetch_count=1, required_api_key=settings.service_api_key),
        RpcServer(conn, settings.rag_rpc_exchange, "rag.quiz.q", settings.rag_quiz_routing_key, quiz_handler, prefetch_count=1, required_api_key=settings.service_api_key),
    ]

    for s in servers:
        await s.start()

    # kick off warmup after consumers are online
    asyncio.create_task(init_rag())

    logger.info("rag-service running", extra={"trace_id": ""})
    # keep alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())