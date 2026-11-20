"""Camada sobre o ChromaDB: persistência, upsert idempotente e consulta com filtros."""
from pathlib import Path

import chromadb

from .embeddings import EmbeddingProvider


class VectorStore:
    """Wrapper enxuto do Chroma com a coleção da aplicação.

    Args:
        persist_dir: Diretório de persistência (criado se não existir).
        embedder: Provedor usado para gerar o embedding_function do Chroma
                  (necessário para que o Chroma saiba embedder queries novas).
    """

    COLLECTION = "knowledge_base"

    def __init__(self, persist_dir: str, embedder: EmbeddingProvider) -> None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._embedder = embedder

        def embed_fn(texts: list[str]) -> list[list[float]]:
            return embedder.embed(texts)

        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION,
            embedding_function=None,
            metadata={"hnsw:space": "cosine"},
        )
        # Mantemos a função de embedding no wrapper: o Chroma recebe vetores prontos.
        self._embed_fn = embed_fn

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        """Insere ou atualiza chunks (ids determinísticos tornam a re-ingestão idempotente)."""
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        query_text: str,
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        """Busca os top_k chunks mais similares, com filtro opcional de metadados."""
        query_embedding = self._embed_fn([query_text])[0]
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters or None,
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            hits.append(
                {
                    "text": doc,
                    "metadata": meta,
                    "score": 1 - dist,  # distância cosseno -> similaridade
                }
            )
        return hits

    def count(self) -> int:
        return self._collection.count()
