"""Rotas da API: chat, saúde e administração da base de conhecimento."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import Pipeline, get_pipeline
from src.generation.schemas import ChatRequest, ChatResponse
from src.prompts.registry import list_versions
from src.ingestion.indexer import ingest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health(pipeline: Pipeline = Depends(get_pipeline)) -> dict:
    """Liveness/readiness + estado da base vetorial."""
    return {
        "status": "ok",
        "environment": pipeline.settings.environment,
        "chunks_indexados": pipeline.vectorstore.count(),
        "llm_provider": pipeline.settings.llm_provider,
        "embedding_provider": pipeline.settings.embedding_provider,
        "prompt_version": pipeline.settings.prompt_version,
    }


@router.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest, pipeline: Pipeline = Depends(get_pipeline)) -> ChatResponse:
    """Endpoint principal: pergunta do passageiro -> resposta com fontes."""
    try:
        return pipeline.service.chat(request)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha no pipeline de chat")
        raise HTTPException(status_code=500, detail="Erro interno no processamento da pergunta") from exc


@router.get("/v1/prompts")
def prompts() -> dict:
    """Lista as versões de system prompt disponíveis (auditoria/A-B test)."""
    return {"prompts": list_versions(), "ativo": get_pipeline().settings.prompt_version}


@router.post("/v1/admin/reingest")
def reingest(pipeline: Pipeline = Depends(get_pipeline)) -> dict:
    """Reindexa a base de conhecimento (idempotente, útil após atualizar documentos)."""
    n = ingest(pipeline.settings, pipeline.vectorstore, pipeline.embedder)
    return {"chunks_indexados": n}
