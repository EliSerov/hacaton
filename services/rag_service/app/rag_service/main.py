import asyncio
import logging

from common.config import AppSettings
from common.logging import setup_logging
from common.rabbit.connection import connect
from common.rabbit.rpc_server import RpcServer
from services.rag_service.app.rag_service.embedder import QueryEmbedder
from services.rag_service.app.rag_service.llm import LlamaCppLLM
from services.rag_service.app.rag_service.mapper import ContractMapper
from services.rag_service.app.rag_service.prompt_builder import PromptBuilder
from services.rag_service.app.rag_service.qdrant_repo import QdrantSearchRepository
from services.rag_service.app.rag_service.retriever import Retriever
from services.rag_service.app.rag_service.service import RagService

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = AppSettings()
    setup_logging(settings.log_level)

    conn = await connect(settings.amqp_url)

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
    rag = RagService(
        embedder=embedder,
        qrepo=qrepo,
        retriever=retriever,
        llm=llm,
        prompt_builder=PromptBuilder(),
        mapper=ContractMapper(),
    )

    # Ensure GPU/LLM single-threaded execution across queues
    gpu_lock = asyncio.Lock()

    async def search_handler(payload: dict, meta: dict) -> dict:
        async with gpu_lock:
            return rag.search(payload, trace_id=meta.get("trace_id", ""))

    async def recommend_handler(payload: dict, meta: dict) -> dict:
        async with gpu_lock:
            return rag.recommend(payload, trace_id=meta.get("trace_id", ""))

    async def quiz_handler(payload: dict, meta: dict) -> dict:
        async with gpu_lock:
            return rag.quiz(payload, trace_id=meta.get("trace_id", ""))

    servers = [
        RpcServer(conn, settings.rag_rpc_exchange, "rag.search.q", settings.rag_search_routing_key, search_handler, prefetch_count=1, required_api_key=settings.service_api_key),
        RpcServer(conn, settings.rag_rpc_exchange, "rag.recommend.q", settings.rag_recommend_routing_key, recommend_handler, prefetch_count=1, required_api_key=settings.service_api_key),
        RpcServer(conn, settings.rag_rpc_exchange, "rag.quiz.q", settings.rag_quiz_routing_key, quiz_handler, prefetch_count=1, required_api_key=settings.service_api_key),
    ]

    for s in servers:
        await s.start()

    logger.info("rag-service running", extra={"trace_id": ""})
    # keep alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
