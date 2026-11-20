"""Orquestra a ingestão: carrega arquivos, divide em chunks e indexa no vector DB."""
import hashlib
import logging
from pathlib import Path

from src.config import Settings
from src.retrieval.embeddings import EmbeddingProvider
from src.retrieval.vectorstore import VectorStore

from .chunking import RecursiveChunker
from .loaders import load_directory

logger = logging.getLogger(__name__)


def _chunk_id(source: str, chunk_index: int, text: str) -> str:
    """ID estável e determinístico (re-ingestão idempotente)."""
    digest = hashlib.sha1(f"{source}:{chunk_index}:{text[:64]}".encode()).hexdigest()
    return digest[:16]


def ingest(settings: Settings, vectorstore: VectorStore, embedder: EmbeddingProvider) -> int:
    """Indexa todo o diretório de conhecimento. Retorna o número de chunks indexados."""
    chunker = RecursiveChunker(chunk_size=500, chunk_overlap=100)
    documents = load_directory(Path(settings.knowledge_dir))

    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunker.split(doc))

    logger.info("Indexando %d chunks de %d documentos...", len(all_chunks), len(documents))

    texts = [c.text for c in all_chunks]
    embeddings = embedder.embed(texts)
    ids = [_chunk_id(c.metadata["source"], c.metadata["chunk_index"], c.text) for c in all_chunks]
    metadatas = [c.metadata for c in all_chunks]

    vectorstore.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return len(all_chunks)
