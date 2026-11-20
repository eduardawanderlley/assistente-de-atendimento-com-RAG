"""Testes dos contratos de saída estruturada."""
import pytest
from pydantic import ValidationError

from src.generation.schemas import AssistantAnswer, ChatRequest


def test_resposta_valida():
    answer = AssistantAnswer(
        resposta="O check-in abre 3 horas antes.",
        fontes=[{"source": "checkin.md", "section": "Check-in", "score": 0.9}],
        confianca=0.9,
        escalonar=False,
        motivo_escalonamento=None,
    )
    assert answer.confianca == 0.9


def test_escalonamento_exige_motivo():
    with pytest.raises(ValidationError):
        AssistantAnswer(
            resposta="Não sei.",
            fontes=[],
            confianca=0.1,
            escalonar=True,
            motivo_escalonamento=None,
        )


def test_confianca_limitada_entre_0_e_1():
    with pytest.raises(ValidationError):
        AssistantAnswer(
            resposta="x",
            fontes=[],
            confianca=1.5,
            escalonar=False,
        )


def test_pergunta_muito_curta_rejeitada():
    with pytest.raises(ValidationError):
        ChatRequest(pergunta="oi")
