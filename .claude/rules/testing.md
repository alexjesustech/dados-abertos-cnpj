> Fonte canônica: seção "Checklist pré-commit" e "API + MCP" de `AGENTS.md` (raiz do projeto).
> Este arquivo é carregado automaticamente pelo Claude Code e contém apenas
> detalhes operacionais específicos do Claude. A regra de negócio/projeto é o AGENTS.md.

### Testes e Lint
- `bin/with-env uv run pytest tests/ -v` (60 unitários, cobertura 100% em `cnpj_lib/`)
- `uv run ruff check .` para lint moderno
- `pylint *.py` para a camada original
