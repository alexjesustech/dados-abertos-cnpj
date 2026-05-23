# CI local — gate único do projeto

> **Por quê?** Este repo **não tem CI cloud** (sem `.github/workflows/`). CI
> local é o único gate automatizado contra regressão de lint/testes. Padrão
> herdado do projeto `nous` (`~/projects/nous/docs/CI-LOCAL.md`), adaptado
> para Python 3.11+ + ruff + pytest.

## Camadas

| Camada | Cobertura | Latência típica |
| :--- | :--- | :--- |
| **`make ci-fast`** | Gate 1 (ruff check + ruff format --check) | < 5s |
| **`make ci`** | Gates 1-2 (ruff + pytest completo) | 10-30s |
| **`make ci-only GATE=<N>`** | Roda apenas um gate (1 ou 2) | Variável |
| **Pre-push hook** | Dispara `make ci-fast` antes de push para `main` | < 5s |

## Pré-requisitos

```bash
# Setup do venv (uma vez):
python3 -m venv .venv
.venv/bin/pip install -e ".[api,mcp,dev]"
```

`ruff` e `pytest` ficam em `.venv/bin/`. O Makefile aponta direto para essas
binárias — não precisa ativar venv antes.

## Camada 1 — `make ci-fast` (uso diário)

```bash
make ci-fast          # ruff check + ruff format --check
```

Rápido (~3-5s). Usado pelo pre-push hook automaticamente.

## Camada 2 — `make ci` (pré-merge completo)

```bash
make ci               # ruff + pytest (toda suite: unit, mcp, integração)
```

Espera-se 10-30s dependendo do tamanho da suite. Suite atual: `tests/unit/`,
`tests/integracao/`, `tests/mcp/`, `tests/smoke_test.py`.

## Camada 3 — `make ci-only GATE=<N>`

```bash
make ci-only GATE=1   # só ruff (lint + format check)
make ci-only GATE=2   # só pytest
```

Alvos individuais granulares:

```bash
make lint             # ruff check
make format           # ruff format (aplica — modifica arquivos)
make format-check     # ruff format --check (verifica sem aplicar)
make test             # pytest tests/
make test-unit        # pytest tests/unit/
make test-mcp         # pytest tests/mcp/
make test-integ       # pytest tests/integracao/
```

## Pre-push hook

### Instalar

```bash
make install-ci-hooks
```

Configura `git config core.hooksPath = .githooks`. A partir daí, todo
`git push origin main` dispara `make ci-fast`. Falha bloqueia.

**Pulado em** `feature/*`, `experiments/*` — commits intermediários não
disparam CI.

### Escape hatch

```bash
CNPJ_SKIP_PREPUSH=1 git push ...
```

Documentar o motivo no commit. Nunca `--no-verify` silencioso (antipadrão
explícito do padrão nous).

### Desinstalar

```bash
make uninstall-ci-hooks
```

## Fluxo recomendado

```
desenvolvimento → make ci-fast (a cada bloco grande, < 5s)
               → make ci-only GATE=2 (se mexeu em teste específico)
               → git commit
               → make ci (antes de push pra main — completo, 10-30s)
               → git push origin main
               → [pre-push: roda ci-fast automaticamente; falha bloqueia]
```

## Auto-fix

`ruff` corrige formatação automaticamente:

```bash
make format                          # ruff format .
.venv/bin/ruff check . --fix         # ruff check com auto-fix (use com cuidado)
```

## Por que não usar `pre-commit` framework, `tox`, `nox`?

- **`pre-commit`** — popular mas exige config YAML separado + venv extra
  por hook. Faz CI virar produto à parte. Não escala bem em monorepo Python.
- **`tox` / `nox`** — bons para matrizes multi-Python (3.10/3.11/3.12) e
  isolar ambientes. Aqui temos um Python único (3.11+) e venv já isolado;
  overhead extra sem ganho.

Decisão: Makefile fino + venv direto é a opção mais leve e versionável.

## Referências

- `~/projects/nous/docs/CI-LOCAL.md` — padrão de origem (Rust + cargo).
- `~/projects/tano/docs/CI-LOCAL.md` — adaptação Laravel/Sail.
- `~/projects/planejamento-financeiro/docs/CI-LOCAL.md` — adaptação Sail-only.
- `Makefile` (raiz) — targets canônicos.
- `.githooks/pre-push` — gate automático em main.
- `pyproject.toml` `[tool.ruff]` `[tool.pytest.ini_options]` — fonte das configs.

## Histórico

- **2026-05-23**: arquivo + Makefile + .githooks/pre-push criados em branch `feature/ci-local-nous-pattern`.
