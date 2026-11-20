# Contribuindo

1. Fork e branch a partir de `main` (`git checkout -b feat/minha-melhoria`);
2. Instale as dependências de dev: `pip install -e ".[dev]"`;
3. Rode os testes e o linter:

```bash
pytest
ruff check .
ruff format --check .
```

4. Abra o PR descrevendo o **porquê** da mudança — o que muda no comportamento
   do assistente importa mais que o código em si.

## Convenções

- Código, commits e PRs em português (o domínio é atendimento ao passageiro BR);
- Type hints em todas as funções públicas;
- Nenhuma chave de API no repositório — configuração sempre via `.env`;
- Mudança de prompt? Nova versão em `src/prompts/`, nunca editar a versão
  `stable` in-place.
