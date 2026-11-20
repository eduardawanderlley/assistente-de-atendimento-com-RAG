"""Injeção de dependências — pipeline RAG construído uma única vez no lifespan."""
import logging
from functools import lru_cache

from src.config import Settings, get_settings
from src.generation.llm import LLMProvider, build_llm
from src.retrieval.embeddings import EmbeddingProvider, build_embedder
from src.retrieval.retriever import Retriever
from src.retrieval.vectorstore import VectorStore
from src.service import RAGService

logger = logging.getLogger(__name__)


class Pipeline:
    """Contêiner com todas as peças do pipeline RAG."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedder: EmbeddingProvider = build_embedder(settings)
        self.vectorstore = VectorStore(settings.chroma_dir, self.embedder)
        self.retriever = Retriever(self.vectorstore, settings)
        self.llm: LLMProvider = build_llm(settings)
        self.service = RAGService(self.retriever, self.llm, settings)

    def ensure_indexed(self) -> None:
        """Indexa a base se o banco vetorial ainda estiver vazio."""
        if self.vectorstore.count() == 0:
            logger.info("Banco vetorial vazio — rodando ingestão inicial...")
            from src.ingestion.indexer import ingest

            n = ingest(self.settings, self.vectorstore, self.embedder)
            logger.info("Ingestão concluída: %d chunks indexados.", n)


@lru_cache
def get_pipeline() -> Pipeline:
    """Singleton do pipeline (uma instância por processo)."""
    return Pipeline(get_settings())
