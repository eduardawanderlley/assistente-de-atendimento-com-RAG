"""Retriever: recuperação com limiar de confiança e filtro por tipo de documento."""
import logging

from src.config import Settings

from .vectorstore import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Orquestra a busca por relevância e aplica guardas de qualidade.

    - Abaixo do score_threshold: o chunk é descartado e sinaliza possível
      pergunta fora da base (dispara escalonamento humano).
    """

    def __init__(self, vectorstore: VectorStore, settings: Settings) -> None:
        self._vectorstore = vectorstore
        self._top_k = settings.top_k
        self._threshold = settings.score_threshold

    def retrieve(self, question: str, doc_type: str | None = None) -> tuple[list[dict], bool]:
        """Retorna (chunks relevantes, needs_escalation)."""
        filters = {"type": doc_type} if doc_type else None
        hits = self._vectorstore.query(question, top_k=self._top_k, filters=filters)

        relevant = [h for h in hits if h["score"] >= self._threshold]
        needs_escalation = len(relevant) == 0

        if needs_escalation:
            logger.warning("Nenhum chunk acima do limiar para: %s", question[:80])
            relevant = hits[:2]  # envia os melhores mesmo assim, para contexto parcial

        return relevant, needs_escalation

    @staticmethod
    def format_context(chunks: list[dict]) -> str:
        """Formata os chunks recuperados para injeção no prompt, com citações rastreáveis."""
        blocks = []
        for i, chunk in enumerate(chunks, start=1):
            meta = chunk["metadata"]
            header = (
                f"[Fonte {i}: {meta.get('source', 'desconhecida')} — seção "
                f'"{meta.get("section", "n/d")}" '
                f"(página {meta.get('pages', 'n/d')}, similaridade {chunk['score']:.2f})]"
            )
            blocks.append(header + "\n" + chunk["text"])
        return "\n\n---\n\n".join(blocks)
