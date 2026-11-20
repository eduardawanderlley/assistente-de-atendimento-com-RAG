# Arquitetura

## Visão geral

O sistema é uma API REST síncrona (FastAPI) que executa o pipeline RAG completo a
cada requisição: **recupera** trechos relevantes da base de conhecimento, **monta**
um prompt versionado com few-shots e contexto citável, e **gera** uma resposta
validada por JSON Schema.

```
Cliente ──POST /v1/chat──► FastAPI ──► RAGService ──► Retriever ──► ChromaDB
                                          │
                                          ├─► PromptRegistry (versão configurada)
                                          │
                                          └─► LLM (OpenAI JSON Schema | Mock)
                                                │
                                                ▼
                                          ChatResponse (validada)
```

## Componentes

### Ingestão (`src/ingestion/`)

| Componente | Responsabilidade |
|---|---|
| `loaders.py` | Extrai texto de `.pdf` (pypdf, por página), `.html/.htm` (BeautifulSoup) e `.md/.txt` |
| `chunking.py` | Divide texto respeitando hierarquia: `##` → `###` → parágrafo → frase → palavra, com overlap configurável |
| `indexer.py` | Orquestra ingestão; gera IDs determinísticos via SHA-1 (fonte + índice + prefixo do texto) |

**Por que chunking recursivo?** Quebrar por tamanho fixo corta conceitos no meio
(ex.: uma política de reembolso dividida entre dois chunks perde sentido). Separar
primeiro por cabeçalhos mantém cada chunk semanticamente coeso.

**Por que IDs determinísticos?** A re-ingestão do mesmo documento gera os mesmos
IDs → `upsert` no Chroma atualiza em vez de duplicar.

### Recuperação (`src/retrieval/`)

- `embeddings.py`: interface `EmbeddingProvider` com duas implementações —
  `LocalEmbeddings` (sentence-transformers, offline, custo zero) e `OpenAIEmbeddings`.
  Ambas normalizam os vetores para similaridade cosseno.
- `vectorstore.py`: wrapper fino sobre `chromadb.PersistentClient`, coleção
  `knowledge_base`, espaço cosseno, consulta com `where` de metadados.
- `retriever.py`: aplica `score_threshold` (default 0.35). Se **nenhum** chunk
  passa no limiar, sinaliza `needs_escalation` — o contexto ainda é enviado, mas a
  resposta final é obrigada a escalar para humano.

### Geração (`src/generation/`)

- `schemas.py`: `AssistantAnswer` é o contrato de saída. O Pydantic valida ranges
  (`confianca ∈ [0,1]`) e invariantes de negócio (`escalonar=True` exige motivo).
- `llm.py`: `OpenAILLM` usa `response_format: json_schema` com `strict: true`;
  `MockLLM` monta a resposta dos chunks para desenvolvimento sem API.

### Prompts (`src/prompts/`)

Prompts são **dados versionados**, não código. `registry.json` documenta autor,
data, status e changelog de cada versão. Trocar `RAG_PROMPT_VERSION` muda o
comportamento do assistente sem redeploy — e `GET /v1/prompts` permite auditoria
e A/B test externo.

## Fluxos

### Fluxo feliz
1. `POST /v1/chat` com `{"pergunta": "..."}`;
2. Retriever busca top-k chunks acima do limiar;
3. Contexto formatado com `[Fonte n: arquivo — seção (score)]`;
4. LLM gera JSON no schema; Pydantic valida;
5. `200 OK` com resposta, fontes e confiança.

### Fluxo de escalonamento
1. Retrieval não encontra nada acima do limiar (ou o LLM marca `escalonar`);
2. Guarda no `RAGService` força `escalonar=True` com motivo padronizado;
3. Cliente exibe "vou chamar um atendente" e roteia para fila humana.

## Trade-offs assumidos

- **Chroma local** em vez de Qdrant/Pinecone: zero infraestrutura para o case;
  a interface `VectorStore` permite trocar depois.
- **Embeddings locais por padrão**: o projeto roda 100% offline; a OpenAI é upgrade,
  não pré-requisito.
- **LLM mock**: prioriza demonstrabilidade. Em produção, use `llm_provider=openai`.
- **Escalonamento como saída estruturada** (não exceção): o cliente decide o
  tratamento (fila, ticket, telefone) — a API não prescreve o canal.
