"""Chunking inteligente: divisão recursiva que respeita hierarquia de títulos.

A ideia é nunca quebrar o texto no meio de um tópico: primeiro tentamos
separar por cabeçalhos Markdown, depois por parágrafos, e só por fim por
frases/palavras. Cada chunk herda metadados de proveniência.
"""
from dataclasses import dataclass, field

from .document import Document

SEPARATORS = ["\n## ", "\n### ", "\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    """Trecho de texto indexável.

    Attributes:
        text: Conteúdo do chunk.
        metadata: Herdado do documento + posição e seção do chunk.
    """

    text: str
    metadata: dict = field(default_factory=dict)


class RecursiveChunker:
    """Divisor recursivo com sobreposição, inspirado no LangChain RecursiveCharacterTextSplitter.

    Args:
        chunk_size: Tamanho máximo de caracteres por chunk.
        chunk_overlap: Sobreposição entre chunks vizinhos (mantém contexto).
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap deve ser menor que chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, document: Document) -> list[Chunk]:
        """Divide um documento em chunks anotados com metadados."""
        raw_chunks = self._split_text(document.content, SEPARATORS)
        chunks = []
        for idx, text in enumerate(raw_chunks):
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        **document.metadata,
                        "chunk_index": idx,
                        "section": self._extract_section(text),
                    },
                )
            )
        return chunks

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Recursão sobre separadores, do mais estrutural ao mais granular."""
        separator = separators[-1]
        for sep in separators:
            if sep in text:
                separator = sep
                break

        splits = text.split(separator)
        good_splits: list[str] = []
        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                # Chunk ainda grande demais: recursão com separadores restantes
                remaining = separators[separators.index(separator) + 1 :]
                good_splits.extend(self._split_text(s, remaining or [" "]))

        return self._merge_splits(good_splits, separator)

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Agrupa splits até o limite de tamanho, com sobreposição configurada."""
        merged: list[str] = []
        current = ""
        for s in splits:
            candidate = s if not current else current + separator + s
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    merged.append(current.strip())
                # Sobreposição: carrega o final do chunk anterior, sem estourar o limite
                tail = current[-self.chunk_overlap :] if current else ""
                overlapped = tail + separator + s if tail else s
                current = overlapped if len(overlapped) <= self.chunk_size else s
        if current.strip():
            merged.append(current.strip())
        return [m for m in merged if m]

    @staticmethod
    def _extract_section(text: str) -> str:
        """Heurística: primeiro cabeçalho ou as primeiras palavras viram identificador de seção."""
        for line in text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                return stripped[:80]
        return " ".join(text.split()[:8])
