"""Central de configuração — todas as variáveis vêm do ambiente (pydantic-settings)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parâmetros da aplicação, sobrescritos por variáveis de ambiente com prefixo RAG_."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="RAG_", extra="ignore")

    app_name: str = "assistente-atendimento-rag"
    environment: str = "dev"

    # Diretórios
    knowledge_dir: str = "data/knowledge_base"
    chroma_dir: str = "data/chroma"

    # Embeddings
    embedding_provider: str = "local"  # local | openai
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # LLM
    llm_provider: str = "mock"  # mock | openai
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"

    # Recuperação
    top_k: int = 4
    score_threshold: float = 0.35

    # Geração
    temperature: float = 0.2
    max_tokens: int = 600

    # Prompts
    prompt_version: str = "v1"


def get_settings() -> Settings:
    """Factory simples (facilita testes com injeção de dependência)."""
    return Settings()
