"""Ponto de entrada da API — uvicorn src.main:app."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.deps import get_pipeline
from src.api.routes import router
from src.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ingestão automática na subida, se o banco vetorial estiver vazio."""
    pipeline = get_pipeline()
    pipeline.ensure_indexed()
    logger.info("API pronta — %d chunks indexados.", pipeline.vectorstore.count())
    yield


app = FastAPI(
    title="Assistente de Atendimento com RAG",
    description=(
        "Chatbot de atendimento a passageiros com RAG sobre a base de conhecimento "
        "do aeroporto (FAQs, políticas e manuais), saída estruturada em JSON e "
        "escalonamento humano quando a confiança é baixa."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/")
def root() -> dict:
    return {"app": "assistente-atendimento-rag", "docs": "/docs", "chat": "/v1/chat"}
