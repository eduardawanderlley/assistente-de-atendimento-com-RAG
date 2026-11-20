"""Provedores de LLM com saída estruturada (JSON Schema).

- OpenAILLM: chat completions com response_format json_schema.
- MockLLM: resposta determinística montada a partir dos chunks (útil para
  demo, testes e desenvolvimento sem custo de API).
"""
import json

from src.config import Settings

from .schemas import ASSISTANT_JSON_SCHEMA, AssistantAnswer


class LLMProvider:
    def generate(self, system: str, messages: list[dict], context: str, question: str) -> AssistantAnswer:
        raise NotImplementedError


class OpenAILLM(LLMProvider):
    """LLM via API OpenAI compatível, forçando saída no JSON Schema."""

    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self._model = settings.llm_model
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens

    def generate(self, system: str, messages: list[dict], context: str, question: str) -> AssistantAnswer:
        completion = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                *messages,
                {
                    "role": "user",
                    "content": json.dumps(
                        {"contexto": context, "pergunta": question}, ensure_ascii=False
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "assistant_answer",
                    "schema": ASSISTANT_JSON_SCHEMA,
                    "strict": True,
                },
            },
        )
        payload = json.loads(completion.choices[0].message.content)
        return AssistantAnswer(**payload)


class MockLLM(LLMProvider):
    """LLM simulado: monta a resposta diretamente dos chunks recuperados.

    Comportamento propositalmente simples e determinístico — serve para
    desenvolver a API e os testes sem depender de chave externa.
    """

    def generate(self, system: str, messages: list[dict], context: str, question: str) -> AssistantAnswer:
        fontes = []
        trechos = []
        for bloco in context.split("---"):
            linha = next((l for l in bloco.splitlines() if l.startswith("[Fonte")), "")
            if "— seção" in linha:
                meta_part = linha.split("— seção")[1]
                section = meta_part.split('"')[1] if '"' in meta_part else "n/d"
                source = linha.split("[Fonte")[1].split(":")[1].strip().split(" ")[0]
                try:
                    score = float(linha.split("similaridade")[1].rstrip("])").strip())
                except (IndexError, ValueError):
                    score = 0.5
                fontes.append({"source": source, "section": section, "score": score})
            texto = bloco.replace(linha, "").strip()
            if texto:
                trechos.append(texto)

        confianca = round(sum(f["score"] for f in fontes) / len(fontes), 2) if fontes else 0.3

        # Heurística do mock: se poucos termos da pergunta aparecem no contexto,
        # a base provavelmente não responde a pergunta -> escalona. É um proxy
        # lexical simples; o LLM real (openai) julga isso semanticamente.
        cobertura = self._cobertura_lexical(question, context)
        if cobertura < 0.5:
            return AssistantAnswer(
                resposta=(
                    "Não encontrei essa informação na nossa base de conhecimento. "
                    "Vou chamar um atendente para ajudar você."
                ),
                fontes=fontes,
                confianca=min(confianca, 0.3),
                escalonar=True,
                motivo_escalonamento=(
                    "Baixa cobertura lexical entre a pergunta e os documentos recuperados "
                    f"({cobertura:.0%} dos termos). A informação provavelmente não está na base."
                ),
            )

        resposta = (
            "Com base na nossa base de conhecimento: "
            + " ".join(trechos)[:900]
        )
        return AssistantAnswer(
            resposta=resposta,
            fontes=fontes,
            confianca=min(confianca, 0.95),
            escalonar=False,
            motivo_escalonamento=None,
        )

    _STOPWORDS = {
        "posso", "preciso", "quanto", "quando", "onde", "qual", "quais", "fazer",
        "como", "porque", "sobre", "antes", "depois", "de", "do", "da", "em",
        "no", "na", "um", "uma", "o", "a", "os", "as", "e", "ou", "para", "com",
        "meu", "minha", "seu", "sua",
    }

    @classmethod
    def _cobertura_lexical(cls, question: str, context: str) -> float:
        """Fração de radicais (4 primeiros caracteres) da pergunta presentes no contexto."""
        import re

        termos = {
            w[:4]
            for w in re.findall(r"[a-zà-ÿ0-9]+", question.lower())
            if len(w) > 3 and w not in cls._STOPWORDS
        }
        if not termos:
            return 1.0
        ctx = context.lower()
        presentes = sum(1 for t in termos if t in ctx)
        return presentes / len(termos)


def build_llm(settings: Settings) -> LLMProvider:
    """Fábrica de provedores de LLM."""
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("RAG_OPENAI_API_KEY obrigatória quando llm_provider=openai")
        return OpenAILLM(settings)
    return MockLLM()
