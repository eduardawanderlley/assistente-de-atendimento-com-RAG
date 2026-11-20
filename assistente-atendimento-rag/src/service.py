"""Camada de serviço: orquestra retrieval + prompt + geração em um único fluxo."""
import json
import logging

from .config import Settings
from .generation.llm import LLMProvider
from .generation.schemas import AssistantAnswer, ChatRequest, ChatResponse
from .prompts.registry import get_prompt, render_few_shots
from .retrieval.retriever import Retriever

logger = logging.getLogger(__name__)


class RAGService:
    """Ponto de entrada do fluxo RAG completo."""

    def __init__(self, retriever: Retriever, llm: LLMProvider, settings: Settings) -> None:
        self._retriever = retriever
        self._llm = llm
        self._settings = settings

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Executa o pipeline: recupera -> monta prompt -> gera resposta estruturada."""
        chunks, needs_escalation = self._retriever.retrieve(request.pergunta, request.doc_type)
        context = self._retriever.format_context(chunks)

        bundle = get_prompt(self._settings.prompt_version)
        few_shot_messages = render_few_shots(bundle.few_shots)

        answer: AssistantAnswer = self._llm.generate(
            system=bundle.system,
            messages=few_shot_messages,
            context=context,
            question=request.pergunta,
        )

        # Guarda de retrieval: se nada passou no limiar, força escalonamento
        if needs_escalation and not answer.escalonar:
            logger.info("Forçando escalonamento por baixa similaridade de retrieval.")
            answer.escalonar = True
            answer.motivo_escalonamento = (
                "Nenhum documento da base teve similaridade suficiente com a pergunta."
            )
            answer.confianca = min(answer.confianca, 0.3)

        return ChatResponse(
            resposta=answer.resposta,
            fontes=answer.fontes,
            confianca=answer.confianca,
            escalonar=answer.escalonar,
            motivo_escalonamento=answer.motivo_escalonamento,
            prompt_version=bundle.version,
            needs_escalation=needs_escalation,
        )
