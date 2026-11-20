"""Modelo de documento bruto carregado da base de conhecimento."""
from dataclasses import dataclass, field


@dataclass
class Document:
    """Documento carregado de um arquivo (PDF, HTML ou Markdown).

    Attributes:
        content: Texto integral extraído do arquivo.
        metadata: Metadados de proveniência (fonte, página, seção etc.).
    """

    content: str
    metadata: dict = field(default_factory=dict)
