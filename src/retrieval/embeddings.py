"""Provedores de embeddings — interface única, implementações trocáveis.

- LocalEmbeddings: sentence-transformers local (padrão, sem chave de API).
- OpenAIEmbeddings: API OpenAI (text-embedding-3-small etc.).
"""
from typing import Protocol

import numpy as np

from src.config import Settings


class EmbeddingProvider(Protocol):
    """Contrato: recebe uma lista de textos e devolve vetores normalizados."""

    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class LocalEmbeddings:
    """Embeddings locais via sentence-transformers (roda offline, custo zero)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dimension = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()


class OpenAIEmbeddings:
    """Embeddings via API OpenAI."""

    DIMENSIONS = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}

    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self.dimension = self.DIMENSIONS.get(model, 1536)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._model, input=texts)
        vectors = [d.embedding for d in response.data]
        return (np.array(vectors) / np.linalg.norm(vectors, axis=1, keepdims=True)).tolist()


def build_embedder(settings: Settings) -> EmbeddingProvider:
    """Fábrica: escolhe o provedor conforme a configuração."""
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("RAG_OPENAI_API_KEY obrigatória quando embedding_provider=openai")
        return OpenAIEmbeddings(settings.embedding_model, settings.openai_api_key, settings.openai_base_url)
    return LocalEmbeddings(settings.embedding_model)
