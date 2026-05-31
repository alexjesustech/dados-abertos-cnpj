# Changelog

Todas as mudanças notáveis deste projeto são documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

> Sem tags Git no repositório até o momento; a versão declarada em
> `pyproject.toml` é `0.1.0`. Os marcos abaixo refletem o histórico real de
> commits em `main`. Promova para `## [0.1.0] - AAAA-MM-DD` e crie a tag
> `v0.1.0` quando for cortar a primeira release.

### Adicionado

- Diretiva de documentação obrigatória + governança documental propagada no
  `CLAUDE.md`/`GEMINI.md` (Definition of Done inclui docs atualizadas).
- Segundo recipient age de recuperação no `.sops.yaml` (GUARD-002).
- Adicionado branch-guard ao hook `.githooks/pre-commit` (bloqueia commit
  direto em `main`/`master`; escape `git config hooks.allowMainCommit true`
  ou `ALLOW_MAIN_COMMIT=1`), compondo com o `gitleaks` já existente. Camada 3
  do fluxo `/branch` da workstation.
- Hook `pre-commit` com `gitleaks` como defesa em profundidade (GUARD-002).
- Padrão "CI local 3 camadas" do projeto `nous` (script de CI local +
  pre-push hook via `core.hooksPath`).

### Alterado

- Restrição estrita sobre `DRAFT.md`: o agente nunca lê, indexa ou referencia
  esse arquivo (revoga a política anterior de "ler-e-formalizar").
- Migração dos segredos do `.env` plaintext legado para **SOPS + age**
  (`.env.sops.yaml` versionado + wrapper `bin/with-env`); `.env` plaintext
  removido (GUARD-002 v0.3.0).
- `GEMINI.md` passou a ser symlink para `CLAUDE.md` (fonte única multi-LLM).
- Aplicado `ruff` (lint + format) em toda a base, resolvendo dívida
  pré-existente que travava o gate de CI.

## Caminho 01 — "Caixa-preta de CNPJ pra mim" (2026-05-23)

> Camada de consumo (A + I + J) entregue em sessão única sobre o banco já
> ingerido (~37 GB, período `2026-05`). Marco principal do projeto.

### Adicionado

- **`cnpj_lib/`** (J) — biblioteca compartilhada: validador de CNPJ
  alfanumérico (Módulo 11, NT Conjunta 2025.001, vigência 06/07/2026),
  formatador e tabelas de domínio RFB. 60 testes + Hypothesis, cobertura 100%.
- **`app/`** (A) — API HTTP local em FastAPI sobre SQLite read-only
  (`?mode=ro`): rotas `/health`, `/periodo-atual`, `/stats`, `/cnpj/{cnpj}`,
  `/cnpj/{basico}/socios`, `/cnpj/{basico}/estabelecimentos`. Pydantic v2,
  Swagger em pt-BR.
- **`mcp_server/`** (I) — MCP server FastMCP `cnpj-br` com 9 tools tipadas
  (`buscar_empresa`, `listar_socios`, `listar_filiais`, `vinculos_pj`,
  `cnaes_por_municipio`, `empresas_por_cnae`, `delta_mensal`, `validar_cnpj`,
  `descrever_codigo`), reusando `app.servicos`; paginação manual
  `limit/offset` + `tem_mais`.
- **`monitor/`** — observabilidade do pipeline (coletor stdlib → `status.json`,
  dashboard HTML em loopback, controle `POST /api/run` e `/api/stop`).
- **`migrations/`** — SQL idempotente com `ANALYZE` + 4 índices.
- Suíte de testes: 27 de integração da API + 37 do MCP; fixtures em
  `tests/conftest.py`.
- `pyproject.toml` com extras `[api]`, `[mcp]`, `[dev]`; entrypoints `cnpj-api`
  e `mcp-cnpj`; gestão via `uv`.
- Série de documentos de produto em `docs/` (planejamento, briefing, relatório,
  backlog) + design system "Dossiê editorial".

## Pipeline WebDAV (2026-05-22)

### Alterado

- **Substituído o scraper Selenium por um fetcher WebDAV** do share público
  Nextcloud da RFB (`fetcher.py`: PROPFIND + GET com `Range`/retry + streaming
  1 MB). POCs Selenium preservadas na branch `experiments/spa-scraping`.
- Projeto renomeado para `dados-abertos-cnpj` (antes `dados_aberto_cpnj` —
  kebab-case + correção de typo).
- README/CLAUDE/GEMINI reescritos refletindo a arquitetura WebDAV.

### Adicionado

- Smoke test do pipeline (`fetcher → database`).

## Baseline — 2024-01-07

### Adicionado

- Criação do projeto: orquestrador de download dos Dados Abertos do CNPJ,
  ingestão por streaming em SQLite local com idempotência via
  `controle_importacao` (`INSERT OR REPLACE`), log em arquivo e notificações
  opcionais Discord/Telegram (`notifier.py`).
