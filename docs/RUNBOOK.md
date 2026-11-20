# Runbook de Operação

## Subir localmente

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Na primeira subida, se o Chroma estiver vazio, a ingestão automática roda via
lifespan. Rode manualmente quando alterar a base:

```bash
python scripts/ingest.py
```

## Docker

```bash
docker compose up --build
# sobe a API na 8000 e já indexa a base antes de aceitar tráfego
```

## Variáveis de ambiente essenciais

| Variável | Default | Descrição |
|---|---|---|
| `RAG_LLM_PROVIDER` | `mock` | `mock` (demo) ou `openai` |
| `RAG_OPENAI_API_KEY` | — | obrigatória se provider = openai |
| `RAG_EMBEDDING_PROVIDER` | `local` | `local` (offline) ou `openai` |
| `RAG_TOP_K` | `4` | chunks recuperados por pergunta |
| `RAG_SCORE_THRESHOLD` | `0.35` | limiar de similaridade p/ escalonamento |
| `RAG_PROMPT_VERSION` | `v1` | versão do system prompt |
| `RAG_KNOWLEDGE_DIR` | `data/knowledge_base` | pasta dos documentos-fonte |

## Endpoints

| Método | Rota | Uso |
|---|---|---|
| GET | `/health` | liveness + estado da base vetorial |
| POST | `/v1/chat` | atendimento ao passageiro |
| GET | `/v1/prompts` | versões de prompt disponíveis e ativa |
| POST | `/v1/admin/reingest` | reindexa a base (idempotente) |

## Troubleshooting

**Respostas sempre escalando** → base vazia ou threshold alto demais; verifique
`/health` (`chunks_indexados`) e ajuste `RAG_SCORE_THRESHOLD`.

**"Versão 'x' não encontrada"** → `RAG_PROMPT_VERSION` não existe no
`registry.json`; confira com `GET /v1/prompts`.

**Primeira resposta lenta** → download do modelo de embeddings local
(~120 MB, sentence-transformers multilíngue); depois fica em cache.

**Mock escalonando demais/pouco** → o MockLLM usa uma heurística de
cobertura lexical (radicais de 4 letras). É apenas um proxy para demo —
em produção, o julgamento semântico é do LLM real (`llm_provider=openai`).

**Trocar o banco vetorial** → implemente a interface de `VectorStore` e injete
via `src/api/deps.py`.
