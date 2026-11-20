# Versionamento de Prompts e Few-Shots

## Estrutura

```
src/prompts/
├── registry.json          # metadados e changelog de cada versão
├── v1/
│   ├── system.md          # system prompt (placeholders: {context}, {question})
│   └── few_shots.json     # pares pergunta/resposta_ideal
└── v2/
    ├── system.md
    └── few_shots.json
```

## Como criar uma nova versão

1. Crie `src/prompts/v3/` copiando a versão anterior;
2. Edite `system.md` e `few_shots.json`;
3. Registre em `registry.json` com `version`, `author`, `date`, `status`
   (`draft` | `beta` | `stable`) e `changelog`;
4. Ative apontando `RAG_PROMPT_VERSION=v3` no `.env`.

A API responde com o campo `prompt_version` em cada mensagem — isso permite
correlacionar feedback de usuários com a versão do prompt que gerou a resposta.

## Diretrizes de qualidade

- **Few-shots devem cobrir os caminhos**: inclua pelo menos um exemplo de resposta
  direta, um de uso de múltiplas fontes e um de escalonamento (ver `v1`);
- **Regras numeradas** no system prompt funcionam melhor que parágrafos de prosa;
- **Nunca** remova uma versão do registry: histórico permite reproduzir qualquer
  comportamento passado;
- Teste mudanças com o mesmo conjunto de perguntas (roadmap: dataset de avaliação).

## Placeholders

O `system.md` é enviado quase como está; contexto e pergunta chegam na última
mensagem do usuário em JSON (`{"contexto": ..., "pergunta": ...}`), garantindo
separação clara entre instrução permanente e dados voláteis.
