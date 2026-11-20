# ✈️ Assistente de Atendimento com RAG

Um chatbot de atendimento a passageiros de aeroporto, construído do zero com **FastAPI**,
**RAG** (Retrieval-Augmented Generation), **ChromaDB**, **embeddings** e **prompt
engineering versionado** — no espírito dos projetos de *GenAI for Customer Experience*
que consultorias como a Capgemini entregam para clientes como a Heathrow.

A ideia é simples e poderosa ao mesmo tempo: em vez de o modelo "decorar" respostas,
ele **busca** nos documentos oficiais do aeroporto (FAQs, políticas, manuais) e responde
**sempre citando a fonte**. E quando não sabe de algo, admite — e escala para um humano.

---

## Por que esse projeto existe

Atendimento automatizado falha de dois jeitos: o robô que inventa resposta (alucinação)
e o robô que trava em qualquer pergunta fora do roteiro. Este projeto ataca os dois:

- **RAG com citações rastreáveis** → cada resposta diz *de qual arquivo e seção* veio a informação;
- **Limiar de similaridade + escalonamento** → pergunta fora da base vira "deixa eu chamar alguém", não uma resposta inventada;
- **Saída estruturada em JSON Schema** → o cliente da API recebe `resposta`, `fontes`, `confianca` e `escalonar` garantidos por contrato.

---

## Arquitetura

```
 pergunta do passageiro
        │
        ▼
┌───────────────────┐
│   FastAPI /v1/chat │
└─────────┬─────────┘
          ▼
┌──────────────────────────┐
│  1. Retrieval (ChromaDB) │  busca por similaridade cosseno
│     + limiar de score    │  (threshold → possível escalonamento)
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│  2. Prompt engineering   │  system prompt versionado + few-shots
│     (registry v1, v2…)   │  + contexto formatado com citações
└─────────┬────────────────┘
          ▼
┌──────────────────────────┐
│  3. Geração estruturada  │  LLM com response_format JSON Schema
│     (OpenAI ou mock)     │  saída validada por Pydantic
└─────────┬────────────────┘
          ▼
   resposta + fontes + confiança + sinal de escalonamento
```

Fluxo de ingestão (roda na subida da API ou via CLI):

```
 PDFs/HTML/Markdown → loaders → chunking recursivo (com overlap e metadados)
                    → embeddings → ChromaDB (ids determinísticos = re-ingestão idempotente)
```

---

## Quickstart

### Pré-requisitos

- Python 3.10+
- (Opcional) chave da OpenAI — **sem ela o projeto roda inteiro em modo demo**, com
  embeddings locais (sentence-transformers) e um LLM mock determinístico.

### 1. Clone e instale

```bash
git clone https://github.com/seu-usuario/assistente-atendimento-rag.git
cd assistente-atendimento-rag

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure (opcional)

```bash
cp .env.example .env
```

Para usar a OpenAI de verdade, edite o `.env`:

```env
RAG_LLM_PROVIDER=openai
RAG_OPENAI_API_KEY=sk-...
RAG_LLM_MODEL=gpt-4o-mini
```

### 3. Suba a API

```bash
uvicorn src.main:app --reload
```

Na primeira subida, a base de conhecimento de exemplo é indexada automaticamente.
Abra <http://localhost:8000/docs> para testar pelo Swagger UI.

### 4. Converse

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "Quanto tempo antes preciso chegar para um voo internacional?"}'
```

Resposta (exemplo real, modo mock):

```json
{
  "resposta": "Com base na nossa base de conhecimento: recomendamos que passageiros de voos internacionais cheguem com 3 horas de antecedência...",
  "fontes": [
    {"source": "checkin.md", "section": "Chegada ao aeroporto", "score": 0.61}
  ],
  "confianca": 0.61,
  "escalonar": false,
  "motivo_escalonamento": null,
  "prompt_version": "v1",
  "needs_escalation": false
}
```

E uma pergunta fora da base, tipo *"posso levar meu furão no avião?"*, retorna
`"escalonar": true` com o motivo — exatamente o que um atendimento sério deve fazer.

---

## Estrutura do projeto

```
.
├── src/
│   ├── main.py                  # app FastAPI + lifespan (ingestão automática)
│   ├── config.py                # configuração via pydantic-settings
│   ├── service.py               # orquestra retrieval + prompt + geração
│   ├── api/
│   │   ├── deps.py              # injeção de dependências (pipeline singleton)
│   │   └── routes.py            # /v1/chat, /health, /v1/prompts, /v1/admin/reingest
│   ├── ingestion/
│   │   ├── loaders.py           # PDF, HTML, Markdown, TXT
│   │   ├── chunking.py          # chunking recursivo com overlap e metadados
│   │   ├── indexer.py           # pipeline de ingestão idempotente
│   │   └── document.py
│   ├── retrieval/
│   │   ├── embeddings.py        # sentence-transformers local OU OpenAI
│   │   ├── vectorstore.py       # wrapper do ChromaDB
│   │   └── retriever.py         # limiar de confiança + formatação de contexto
│   ├── prompts/
│   │   ├── registry.py          # carrega prompts versionados
│   │   ├── registry.json        # changelog das versões
│   │   ├── v1/                  # system.md + few_shots.json
│   │   └── v2/                  # versão beta (A/B test)
│   └── generation/
│       ├── llm.py               # OpenAI (JSON Schema) OU mock determinístico
│       └── schemas.py           # contratos Pydantic da saída
├── data/knowledge_base/         # base de conhecimento de exemplo (aeroporto)
├── scripts/ingest.py            # CLI de re-ingestão manual
├── tests/                       # pytest (chunking, schemas, prompts, retriever)
├── docs/                        # arquitetura, versionamento de prompts, runbook
├── Dockerfile / docker-compose.yml
└── README.md
```

---

## Documentação

| Documento | O que você encontra lá |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Decisões de design, fluxos e trade-offs |
| [docs/PROMPTS.md](docs/PROMPTS.md) | Como versionar prompts e few-shots |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Operação: ingestão, troubleshooting, Docker |

---

## Decisões de design em 30 segundos

- **ChromaDB** por ser open source, persistente e sem servidor — suba e use;
- **Chunking recursivo** que respeita cabeçalhos antes de quebrar por parágrafo/frase;
- **IDs determinísticos** (hash de fonte + índice + texto) → re-ingestão idempotente, sem duplicatas;
- **Prompts como dados versionados** em `src/prompts/`, com `registry.json` de changelog — troca de versão é mudar uma env var, não um deploy;
- **JSON Schema estrito** no `response_format` + validação Pydantic dupla → clientes nunca recebem saída malformada;
- **Modo mock** para dev/testes sem custo de API — o mesmo contrato, resposta determinística (com heurística de cobertura lexical para demonstrar o escalonamento);
- **Embeddings multilíngues por padrão** (`paraphrase-multilingual-MiniLM-L12-v2`) — pensado para bases em português.

## Roadmap

- [ ] Histórico de conversa por `session_id` (memória curta no contexto)
- [ ] Híbrido BM25 + denso (reciprocal rank fusion)
- [ ] Reranker (ex.: bge-reranker) sobre os top-k
- [ ] Upload de documentos em runtime (`POST /v1/admin/documents`)
- [ ] Avaliação contínua: dataset de perguntas + métricas de faithfulness
- [ ] Observabilidade: tracing do pipeline (Langfuse/OpenTelemetry)

## Contribuindo

Issues e PRs são bem-vindos! Rode `pytest` antes de abrir um PR e mantenha o estilo
com `ruff check . && ruff format .`. Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

MIT — use à vontade, e boas vendas no case de entrevista. 😉
