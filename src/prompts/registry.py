"""Registro de system prompts versionados.

Cada versão vive em `prompts/<versao>/` com dois arquivos:
- `system.md`: o system prompt (markdown, com placeholders {context} e {question}).
- `few_shots.json`: exemplos de pares pergunta/resposta ideais.

`prompts/registry.json` documenta cada versão (autor, data, changelog). A API
expondo o prompt_ativo na resposta torna o comportamento auditável e permite
A/B test entre versões.
"""
import json
from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


@dataclass
class PromptBundle:
    """System prompt + few-shots de uma versão."""

    version: str
    system: str
    few_shots: list[dict]


def _load_registry() -> dict:
    with open(PROMPTS_DIR / "registry.json", encoding="utf-8") as f:
        return json.load(f)


def list_versions() -> list[dict]:
    """Retorna as versões registradas, da mais recente para a mais antiga."""
    return _load_registry()["versions"]


def get_prompt(version: str) -> PromptBundle:
    """Carrega o system prompt e os few-shots de uma versão.

    Raises:
        KeyError: se a versão não existe no registry.
    """
    versions = {v["version"]: v for v in _load_registry()["versions"]}
    if version not in versions:
        raise KeyError(
            f"Versão '{version}' não encontrada. Disponíveis: {sorted(versions)}"
        )

    version_dir = PROMPTS_DIR / version
    system = (version_dir / "system.md").read_text(encoding="utf-8")
    with open(version_dir / "few_shots.json", encoding="utf-8") as f:
        few_shots = json.load(f)

    return PromptBundle(version=version, system=system, few_shots=few_shots)


def render_few_shots(few_shots: list[dict]) -> str:
    """Serializa os few-shots para o formato de mensagens da API."""
    messages = []
    for shot in few_shots:
        messages.append({"role": "user", "content": shot["pergunta"]})
        messages.append({"role": "assistant", "content": json.dumps(shot["resposta_ideal"], ensure_ascii=False)})
    return messages
