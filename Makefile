# ============================================================================
# dados-abertos-cnpj — Makefile
# Pipeline + API + MCP server (Python 3.11+)
# ============================================================================
#
# Uso: make <target>
# Help: make help (default)
#
# Convenção: ferramentas rodam via venv local (`.venv/bin/<tool>`).
# Se o venv não existe, criar com: python3 -m venv .venv && .venv/bin/pip install -e ".[api,mcp,dev]"
# ============================================================================

.DEFAULT_GOAL := help

VENV := .venv/bin
RUFF := $(VENV)/ruff
PYTEST := $(VENV)/pytest

.PHONY: help ci ci-fast ci-only \
        gate-1 gate-2 \
        install-ci-hooks uninstall-ci-hooks \
        lint format format-check test test-unit test-mcp test-integ

help: ## Lista targets disponíveis
	@echo "Targets:"
	@grep -E '^[a-z_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk -F':.*## ' '{printf "  %-22s %s\n", $$1, $$2}'

# ============================================================================
# CI LOCAL — padrão 3-camadas (ref: docs/CI-LOCAL.md, projeto nous)
# ============================================================================
# Motivação: repo sem CI cloud. CI local é o ÚNICO gate automatizado contra
# regressão de lint/testes. Adotado em 2026-05-23.
# ============================================================================

ci: gate-1 gate-2 ## Pipeline CI completa (ruff + pytest)
	@echo ""
	@echo "✅ CI completa — todos os gates passaram"

ci-fast: gate-1 ## CI rápido (ruff check + format check) — < 5s, usado pelo pre-push hook
	@echo ""
	@echo "✅ CI fast — lint ok (pula pytest)"

ci-only: ## Roda apenas um gate. Uso: make ci-only GATE=1 (ou 2)
	@if [ -z "$(GATE)" ]; then echo "Uso: make ci-only GATE=<1|2>" >&2; exit 2; fi
	@$(MAKE) gate-$(GATE)

gate-1: lint format-check ## Gate 1 — Lint (ruff check + format check)
	@echo "✅ Gate 1 — Lint"

gate-2: test ## Gate 2 — Testes (pytest unit + integração + mcp)
	@echo "✅ Gate 2 — Testes"

# ============================================================================
# FERRAMENTAS
# ============================================================================

lint: ## ruff check
	@echo "▸ ruff check"
	@$(RUFF) check .

format: ## ruff format (aplica)
	@echo "▸ ruff format (aplica)"
	@$(RUFF) format .

format-check: ## ruff format --check (verifica sem aplicar)
	@echo "▸ ruff format --check"
	@$(RUFF) format --check .

test: ## pytest (toda a suite)
	@echo "▸ pytest"
	@$(PYTEST) tests/

test-unit: ## pytest unit
	@$(PYTEST) tests/unit/

test-mcp: ## pytest mcp
	@$(PYTEST) tests/mcp/

test-integ: ## pytest integração
	@$(PYTEST) tests/integracao/

# ============================================================================
# HOOKS GIT
# ============================================================================

install-ci-hooks: ## Ativa .githooks/ como core.hooksPath (pre-push roda 'make ci-fast' em main)
	@git config core.hooksPath .githooks
	@echo "✅ core.hooksPath = .githooks"
	@echo "   pre-push: dispara 'make ci-fast' em push pra main"
	@echo "   Escape: CNPJ_SKIP_PREPUSH=1 git push (documentar por quê)"

uninstall-ci-hooks: ## Remove core.hooksPath
	@git config --unset core.hooksPath || true
	@echo "✅ core.hooksPath removido"
