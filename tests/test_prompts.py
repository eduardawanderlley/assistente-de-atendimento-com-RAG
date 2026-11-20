"""Testes do registro de prompts versionados."""
import pytest

from src.prompts.registry import get_prompt, list_versions, render_few_shots


def test_registry_tem_versoes():
    versions = list_versions()
    assert any(v["version"] == "v1" for v in versions)


def test_carrega_prompt_v1():
    bundle = get_prompt("v1")
    assert "Skylla" in bundle.system
    assert len(bundle.few_shots) >= 1


def test_versao_inexistente_levanta_erro():
    with pytest.raises(KeyError):
        get_prompt("v99")


def test_render_few_shots_alterna_papeis():
    bundle = get_prompt("v1")
    messages = render_few_shots(bundle.few_shots)
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
