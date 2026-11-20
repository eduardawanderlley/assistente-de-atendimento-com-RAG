<div align="center">

# Enterprise RAG Customer Support Assistant

**Production-ready Retrieval-Augmented Generation (RAG) API built for high-stakes customer operations, featuring traceable citations, confidence-based human escalation, versioned prompt registries, and strict JSON Schema contracts.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[🇺🇸 English](#english-documentation) • [🇧🇷 Português](#documentação-em-português)

</div>

---

## English Documentation

### Overview

Enterprise customer support automation typically fails in two ways: **hallucination** (fabricating policies when context is missing) or **brittleness** (failing completely on out-of-scope queries).

Designed around enterprise *GenAI for Customer Experience* patterns (such as airport passenger operations), this system enforces strict guardrails between knowledge retrieval and response generation:

- **Grounded Generation with Traceable Citations:** Every answer is strictly anchored to retrieved documents, returning exact file names, section headers, and similarity scores.
- **Deterministic Human Escalation:** Queries falling below a configurable cosine similarity threshold automatically trigger an escalation flag (`escalonar: true`) with structured reasoning, preventing fabricated answers.
- **Contract-First Structured Outputs:** Enforces OpenAI Structured Outputs (JSON Schema) paired with Pydantic validation, guaranteeing predictable payloads for downstream integrations.
- **Decoupled Prompt Registry:** Prompts and few-shot examples are managed as versioned artifacts (`v1`, `v2`), enabling A/B testing and instant rollbacks via environment variables without code deployments.
- **Zero-Cost Local Demo Mode:** Runs out-of-the-box without external API keys using local multilingual embeddings (`sentence-transformers`) and a deterministic mock LLM with lexical coverage heuristics.

---

### System Architecture

#### Online Inference Pipeline (`/v1/chat`)

```text
  Passenger Query
         │
         ▼
┌─────────────────────┐
│ FastAPI  /v1/chat   │  Input validation & dependency injection
└──────────┬──────────┘
           ▼
┌─────────────────────────────┐
│ 1. Semantic Retrieval       │  ChromaDB cosine similarity search
│    & Confidence Gate        │  Evaluates score against threshold
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 2. Prompt Assembly          │  Loads versioned system prompt + few-shots
│    (Registry v1, v2...)     │  Injects formatted context & metadata
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 3. Constrained Generation   │  OpenAI (JSON Schema) or Deterministic Mock
│    & Contract Validation    │  Double-validated via Pydantic schemas
└──────────┬──────────────────┘
           ▼
  Structured Payload (Answer + Citations + Confidence + Escalation Signal)
```

#### Offline / Startup Ingestion Pipeline

```text
  Raw Documents (PDF, HTML, MD, TXT)
         │
         ▼
  Format-Specific Loaders
         │
         ▼
  Structure-Aware Recursive Chunking (Preserves headers + overlap + metadata)
         │
         ▼
  Multilingual Embeddings (paraphrase-multilingual-MiniLM-L12-v2 or OpenAI)
         │
         ▼
  ChromaDB Upsert (Deterministic SHA-256 IDs → Idempotent re-ingestion)
```

---

### Quickstart

#### Prerequisites
- Python 3.10+
- *(Optional)* OpenAI API Key — **not required for local evaluation**. Without a key, the system defaults to local embeddings and a deterministic mock generator.

#### 1. Installation

```bash
git clone [https://github.com/your-username/assistente-atendimento-rag.git](https://github.com/your-username/assistente-atendimento-rag.git)
cd assistente-atendimento-rag

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

#### 2. Environment Configuration (Optional)

```bash
cp .env.example .env
```

To enable live OpenAI inference, update `.env`:

```env
RAG_LLM_PROVIDER=openai
RAG_OPENAI_API_KEY=sk-...
RAG_LLM_MODEL=gpt-4o-mini
```

#### 3. Start the API Server

```bash
uvicorn src.main:app --reload
```

On initial startup, the FastAPI lifespan manager automatically ingests the sample airport knowledge base (`data/knowledge_base/`). Interactive API documentation is available at `http://localhost:8000/docs`.

#### 4. Usage Examples

**In-Scope Query (Grounded Response):**

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "Quanto tempo antes preciso chegar para um voo internacional?"}'
```

```json
{
  "resposta": "Com base na nossa base de conhecimento: recomendamos que passageiros de voos internacionais cheguem com 3 horas de antecedência...",
  "fontes": [
    {
      "source": "checkin.md",
      "section": "Chegada ao aeroporto",
      "score": 0.61
    }
  ],
  "confianca": 0.61,
  "escalonar": false,
  "motivo_escalonamento": null,
  "prompt_version": "v1",
  "needs_escalation": false
}
```

**Out-of-Scope Query (Graceful Escalation):**

Querying `"posso levar meu furão no avião?"` (unindexed policy) evaluates below the similarity threshold and returns `"escalonar": true` with an explicit escalation reason, routing the passenger to a human agent.

---

### Architectural Decisions & Trade-offs

| Component | Decision | Rationale |
| :--- | :--- | :--- |
| **Vector Store** | **ChromaDB** | Zero-infrastructure, local persistence, fast prototyping-to-container workflow. |
| **Chunking** | **Header-Aware Recursive** | Splits by Markdown/document hierarchy before falling back to paragraphs, preserving semantic boundaries. |
| **Idempotency** | **Deterministic Hashing** | Chunk IDs are derived from `hash(source + index + content)`, preventing vector duplication across re-runs. |
| **Prompt Ops** | **File-Based Registry** | Prompts live in `src/prompts/{version}/` with a `registry.json` changelog, decoupling prompt tuning from application releases. |
| **Reliability** | **Strict JSON Schema + Pydantic** | Eliminates downstream parsing errors by enforcing schema adherence at the model decoding layer. |
| **Embeddings** | **Multilingual MiniLM** | `paraphrase-multilingual-MiniLM-L12-v2` provides strong semantic alignment for Portuguese corpora out-of-the-box. |

---

### Project Structure

```text
.
├── src/
│   ├── main.py                  # FastAPI entry point & startup ingestion lifespan
│   ├── config.py                # Type-safe settings via pydantic-settings
│   ├── service.py               # Core orchestrator (Retrieval → Prompt → Generation)
│   ├── api/
│   │   ├── deps.py              # Dependency injection (pipeline singletons)
│   │   └── routes.py            # /v1/chat, /health, /v1/prompts, /v1/admin/reingest
│   ├── ingestion/
│   │   ├── loaders.py           # Multi-format parsers (PDF, HTML, Markdown, TXT)
│   │   ├── chunking.py          # Recursive splitter with metadata preservation
│   │   ├── indexer.py           # Idempotent vector indexing pipeline
│   │   └── document.py          # Internal document domain models
│   ├── retrieval/
│   │   ├── embeddings.py        # Strategy pattern: Local SentenceTransformers vs. OpenAI
│   │   ├── vectorstore.py       # ChromaDB abstraction layer
│   │   └── retriever.py         # Similarity threshold filtering & context formatting
│   ├── prompts/
│   │   ├── registry.py          # Dynamic prompt loader
│   │   ├── registry.json        # Version metadata & changelog
│   │   ├── v1/                  # Production baseline (system.md + few_shots.json)
│   │   └── v2/                  # Experimental candidate (A/B testing)
│   └── generation/
│       ├── llm.py               # OpenAI Structured Outputs & Deterministic Mock
│       └── schemas.py           # Strict Pydantic response contracts
├── data/knowledge_base/         # Sample airport passenger operations corpus
├── scripts/ingest.py            # CLI utility for manual re-ingestion
├── tests/                       # Unit & integration test suite (pytest)
├── docs/                        # Extended architecture, prompt ops, and runbooks
├── Dockerfile
└── docker-compose.yml
```

---

### Extended Documentation

- **[Architecture & Trade-offs](docs/ARCHITECTURE.md):** Deep dive into retrieval mechanics, scoring heuristics, and system boundaries.
- **[Prompt Versioning Guide](docs/PROMPTS.md):** Workflows for creating, testing, and promoting prompt versions.
- **[Operations Runbook](docs/RUNBOOK.md):** Docker deployment, manual ingestion CLI, and troubleshooting.

---

### Roadmap

- [ ] **Conversational Memory:** Session-scoped history management via `session_id`.
- [ ] **Hybrid Search:** Combining sparse (BM25) and dense vector retrieval via Reciprocal Rank Fusion (RRF).
- [ ] **Cross-Encoder Reranking:** Second-stage relevance scoring (e.g., `bge-reranker`) on top-k candidates.
- [ ] **Dynamic Ingestion API:** Runtime document upload and indexing (`POST /v1/admin/documents`).
- [ ] **Automated RAG Evaluation:** Golden dataset benchmarking measuring *Faithfulness* and *Answer Relevance* (RAGAS).
- [ ] **Production Observability:** End-to-end latency and token tracing via OpenTelemetry / Langfuse.

---

### Contributing & License

Contributions are welcome. Please ensure all tests pass (`pytest`) and code adheres to formatting standards (`ruff check . && ruff format .`) prior to opening a Pull Request. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Distributed under the **MIT License**. See `LICENSE` for more information.

---
---

## Documentação em Português

### Visão Geral

Sistemas de atendimento automatizado costumam falhar por dois motivos principais: **alucinação** (inventar políticas quando não há contexto suficiente) ou **rigidez** (travar diante de perguntas fora do escopo mapeado).

Projetado com base em arquiteturas corporativas de *GenAI for Customer Experience* (aplicadas a operações aeroportuárias), este sistema estabelece barreiras rigorosas entre a recuperação de conhecimento e a geração de respostas:

- **Geração Ancorada com Citações Rastreáveis:** Toda resposta é estritamente vinculada aos documentos recuperados, retornando o arquivo de origem, a seção exata e o score de similaridade.
- **Escalonamento Humano Determinístico:** Perguntas abaixo do limiar de similaridade cosseno acionam automaticamente a flag de transbordo (`escalonar: true`) com justificativa estruturada, eliminando respostas inventadas.
- **Contratos de Saída Estruturados:** Utiliza *Structured Outputs* (JSON Schema) combinados com validação Pydantic, garantindo previsibilidade para sistemas integradores.
- **Registro Versionado de Prompts:** Prompts e exemplos (*few-shots*) são gerenciados como artefatos versionados (`v1`, `v2`), permitindo testes A/B e *rollbacks* via variáveis de ambiente sem necessidade de novo deploy.
- **Modo Demonstração Local (Custo Zero):** Executa integralmente sem chaves de API externas, utilizando *embeddings* locais multilíngues (`sentence-transformers`) e um motor LLM mock determinístico com heurística de cobertura lexical.

---

### Arquitetura do Sistema

#### Fluxo de Inferência Online (`/v1/chat`)

```text
  Pergunta do Passageiro
         │
         ▼
┌─────────────────────┐
│ FastAPI  /v1/chat   │  Validação de entrada e injeção de dependências
└──────────┬──────────┘
           ▼
┌─────────────────────────────┐
│ 1. Retrieval Semântico      │  Busca por similaridade cosseno no ChromaDB
│    & Gate de Confiança      │  Avaliação do score frente ao limiar (threshold)
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 2. Engenharia de Prompt     │  Carrega system prompt + few-shots versionados
│    (Registry v1, v2...)     │  Injeta contexto formatado com metadados
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 3. Geração Estruturada      │  OpenAI (JSON Schema) ou Mock Determinístico
│    & Validação de Contrato  │  Dupla validação via schemas Pydantic
└──────────┬──────────────────┘
           ▼
  Payload Estruturado (Resposta + Fontes + Confiança + Sinal de Escalonamento)
```

#### Fluxo de Ingestão (Startup ou CLI)

```text
  Documentos Brutos (PDF, HTML, MD, TXT)
         │
         ▼
  Loaders Específicos por Formato
         │
         ▼
  Chunking Recursivo Estrutural (Preserva cabeçalhos + overlap + metadados)
         │
         ▼
  Embeddings Multilíngues (paraphrase-multilingual-MiniLM-L12-v2 ou OpenAI)
         │
         ▼
  Upsert no ChromaDB (IDs SHA-256 determinísticos → Re-ingestão idempotente)
```

---

### Guia Rápido (Quickstart)

#### Pré-requisitos
- Python 3.10+
- *(Opcional)* Chave de API da OpenAI — **dispensável para avaliação local**. Sem a chave, o projeto opera com *embeddings* locais e gerador mock determinístico.

#### 1. Instalação

```bash
git clone [https://github.com/seu-usuario/assistente-atendimento-rag.git](https://github.com/seu-usuario/assistente-atendimento-rag.git)
cd assistente-atendimento-rag

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

#### 2. Configuração de Ambiente (Opcional)

```bash
cp .env.example .env
```

Para utilizar a API da OpenAI em produção, edite o arquivo `.env`:

```env
RAG_LLM_PROVIDER=openai
RAG_OPENAI_API_KEY=sk-...
RAG_LLM_MODEL=gpt-4o-mini
```

#### 3. Inicialização da API

```bash
uvicorn src.main:app --reload
```

Na primeira execução, o gerenciador de ciclo de vida (*lifespan*) do FastAPI indexa automaticamente a base de conhecimento de exemplo (`data/knowledge_base/`). A documentação interativa (Swagger UI) fica disponível em `http://localhost:8000/docs`.

#### 4. Exemplos de Uso

**Pergunta Coberta pela Base (Resposta Ancorada):**

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "Quanto tempo antes preciso chegar para um voo internacional?"}'
```

```json
{
  "resposta": "Com base na nossa base de conhecimento: recomendamos que passageiros de voos internacionais cheguem com 3 horas de antecedência...",
  "fontes": [
    {
      "source": "checkin.md",
      "section": "Chegada ao aeroporto",
      "score": 0.61
    }
  ],
  "confianca": 0.61,
  "escalonar": false,
  "motivo_escalonamento": null,
  "prompt_version": "v1",
  "needs_escalation": false
}
```

**Pergunta Fora da Base (Escalonamento Seguro):**

Ao consultar *"posso levar meu furão no avião?"* (regra inexistente na base), o sistema detecta baixa similaridade semântica e retorna `"escalonar": true` acompanhado do motivo técnico, direcionando o atendimento para um operador humano.

---

### Decisões Arquiteturais e Trade-offs

| Componente | Decisão | Justificativa Técnica |
| :--- | :--- | :--- |
| **Banco Vetorial** | **ChromaDB** | Persistência local sem dependências de infraestrutura externa; ideal para inicialização rápida e conteinerização. |
| **Chunking** | **Recursivo Estrutural** | Prioriza quebras por hierarquia de cabeçalhos antes de dividir parágrafos, preservando a integridade semântica. |
| **Idempotência** | **Hashing Determinístico** | IDs gerados via `hash(fonte + índice + conteúdo)`, evitando duplicação de vetores em re-indexações. |
| **Prompt Ops** | **Registry Versionado** | Prompts isolados em `src/prompts/{versão}/` com changelog em `registry.json`, desacoplando ajustes de prompt do ciclo de deploy. |
| **Confiabilidade** | **JSON Schema + Pydantic** | Elimina falhas de *parsing* nos clientes da API ao impor validação estrutural na camada de geração. |
| **Embeddings** | **MiniLM Multilíngue** | O modelo `paraphrase-multilingual-MiniLM-L12-v2` oferece alta precisão semântica nativa para bases em português. |

---

### Documentação Complementar

- **[Arquitetura e Trade-offs](docs/ARCHITECTURE.md):** Detalhamento dos fluxos de recuperação, heurísticas de score e limites do sistema.
- **[Versionamento de Prompts](docs/PROMPTS.md):** Boas práticas para criação, validação e promoção de versões de prompts.
- **[Runbook Operacional](docs/RUNBOOK.md):** Deploy com Docker, CLI de ingestão manual e resolução de problemas.

---

### Roadmap

- [ ] **Memória Conversacional:** Histórico de contexto por sessão via `session_id`.
- [ ] **Busca Híbrida:** Combinação de busca lexical (BM25) e vetorial densa via *Reciprocal Rank Fusion* (RRF).
- [ ] **Reranking:** Reclassificação semântica de segunda etapa (ex.: `bge-reranker`) sobre os candidatos *top-k*.
- [ ] **Ingestão Dinâmica via API:** Upload e indexação de documentos em tempo de execução (`POST /v1/admin/documents`).
- [ ] **Avaliação Contínua (RAG Eval):** Pipeline automatizado de métricas de *Faithfulness* e *Answer Relevance* (RAGAS).
- [ ] **Observabilidade:** Rastreamento ponta a ponta de latência e consumo de tokens via OpenTelemetry / Langfuse.

---

### Contribuição e Licença

Contribuições são bem-vindas. Certifique-se de executar a suíte de testes (`pytest`) e manter a padronização de código (`ruff check . && ruff format .`) antes de abrir um Pull Request. Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

Distribuído sob a licença **MIT**. Consulte o arquivo `LICENSE` para mais informações.
```
