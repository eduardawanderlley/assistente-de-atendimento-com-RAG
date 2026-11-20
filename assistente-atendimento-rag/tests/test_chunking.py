"""Testes do chunker recursivo."""
from src.ingestion.chunking import RecursiveChunker


def test_chunker_respeita_tamanho_maximo(sample_document):
    chunker = RecursiveChunker(chunk_size=120, chunk_overlap=20)
    chunks = chunker.split(sample_document)
    assert len(chunks) > 1
    assert all(len(c.text) <= 120 for c in chunks)


def test_chunker_preserva_metadados(sample_document):
    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=10)
    chunks = chunker.split(sample_document)
    for chunk in chunks:
        assert chunk.metadata["source"] == "exemplo.md"
        assert "chunk_index" in chunk.metadata
        assert "section" in chunk.metadata


def test_overlap_menor_que_tamanho():
    import pytest

    with pytest.raises(ValueError):
        RecursiveChunker(chunk_size=100, chunk_overlap=100)
