"""Schemas Pydantic — contrato de saída estruturada (JSON Schema) do assistente.

A resposta SEMPRE sai validada por estes schemas: a API e os clientes
podem confiar nos campos `fontes`, `confianca` e `escalonar`.
"""
from pydantic import BaseModel, Field


class CitedSource(BaseModel):
    """Fonte citada na resposta, rastreável até um chunk da base."""

    source: str = Field(..., description="Nome do arquivo de origem")
    section: str = Field(..., description="Seção/trecho de onde a informação veio")
    score: float = Field(..., description="Similaridade do chunk recuperado (0 a 1)")


class AssistantAnswer(BaseModel):
    """Contrato de saída do LLM — validado antes de chegar ao usuário."""

    resposta: str = Field(..., description="Resposta em português, clara e objetiva")
    fontes: list[CitedSource] = Field(default_factory=list, description="Fontes usadas")
    confianca: float = Field(..., ge=0, le=1, description="Confiança da resposta (0 a 1)")
    escalonar: bool = Field(False, description="True se a dúvida deve ir para um atendente humano")
    motivo_escalonamento: str | None = Field(None, description="Por que escalonar (obrigatório se escalonar=True)")

    def model_post_init(self, __context: object) -> None:
        """Guarda simples: escalonamento sem motivo não passa."""
        if self.escalonar and not self.motivo_escalonamento:
            raise ValueError("motivo_escalonamento é obrigatório quando escalonar=True")


ASSISTANT_JSON_SCHEMA = AssistantAnswer.model_json_schema()


class ChatRequest(BaseModel):
    """Payload do endpoint POST /v1/chat."""

    pergunta: str = Field(..., min_length=3, max_length=2000, description="Pergunta do passageiro")
    doc_type: str | None = Field(None, description="Filtrar busca por tipo: pdf | html | md")
    session_id: str | None = Field(None, description="ID de conversa (para histórico futuro)")


class ChatResponse(BaseModel):
    """Resposta da API ao cliente."""

    resposta: str
    fontes: list[CitedSource]
    confianca: float
    escalonar: bool
    motivo_escalonamento: str | None
    prompt_version: str
    needs_escalation: bool = Field(False, description="True quando a recuperação falhou (limiar)")
