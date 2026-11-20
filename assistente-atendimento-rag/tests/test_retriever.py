"""Testes do retriever com vector store em memória (embeddings falsos)."""
from src.config import Settings
from src.retrieval.retriever import Retriever
from src.retrieval.vectorstore import VectorStore


class FakeEmbedder:
    dimension = 8

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Embedding fake: bag-of-chars normalizado — suficiente p/ teste de integração
        vectors = []
        for t in texts:
            v = [0.0] * self.dimension
            for ch in t.lower():
                v[ord(ch) % self.dimension] += 1.0
            norm = sum(x * x for x in v) ** 0.5 or 1.0
            vectors.append([x / norm for x in v])
        return vectors


def _build_store(tmp_path) -> VectorStore:
    store = VectorStore(str(tmp_path), FakeEmbedder())
    embedder = FakeEmbedder()
    texts = ["check-in abre tres horas antes do embarque", "estacionamento custa 60 reais"]
    store.upsert(
        ids=["a", "b"],
        embeddings=embedder.embed(texts),
        documents=texts,
        metadatas=[{"source": "x.md", "section": "s", "type": "md"}] * 2,
    )
    return store


def test_recupera_chunk_relevante(tmp_path):
    settings = Settings(top_k=2, score_threshold=0.0)
    retriever = Retriever(_build_store(tmp_path), settings)
    chunks, needs_escalation = retriever.retrieve("quanto custa o estacionamento")
    assert not needs_escalation
    assert len(chunks) >= 1


def test_sem_resultado_sinaliza_escalonamento(tmp_path):
    settings = Settings(top_k=2, score_threshold=0.999)
    retriever = Retriever(_build_store(tmp_path), settings)
    chunks, needs_escalation = retriever.retrieve("quanto custa o estacionamento")
    assert needs_escalation
    assert len(chunks) >= 1  # envia os melhores mesmo assim, para contexto parcial


def test_format_context_tem_fonte_rastreavel(tmp_path):
    settings = Settings(top_k=1, score_threshold=0.0)
    retriever = Retriever(_build_store(tmp_path), settings)
    chunks, _ = retriever.retrieve("estacionamento")
    context = retriever.format_context(chunks)
    assert "[Fonte 1" in context
    assert "x.md" in context
