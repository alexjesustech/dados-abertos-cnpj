# Changelog

Todas as mudanças notáveis deste projeto são documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado

- Seção `## Status` (maturidade SemVer) no README, `LICENSE` MIT e seção `## Licença`.
- `llms.txt` na raiz (padrão [llmstxt.org](https://llmstxt.org/)).
- `AGENTS.md` como guia público de agente: arquitetura, comandos, convenções de
  código e política de segredos.

### Alterado

- Migração dos segredos do `.env` plaintext legado para **SOPS + age**
  (arquivo cifrado **não versionado** + wrapper `bin/with-env`); `.env` plaintext removido.

### Removido

- Configuração local de tooling de IA (`.claude/`, `.opencode/`, `CLAUDE.md`,
  `GEMINI.md`, `opencode.json`), arquivos cifrados de segredo (`*.sops.yaml`) e
  planejamento interno (`docs/HANDOFF.md`) saem do versionamento e passam a
  **local-only** — a orientação pública de agente fica no `AGENTS.md`.

### Corrigido

- Removidos caminhos absolutos pessoais dos exemplos de configuração (higiene pública).

> A versão declarada em `pyproject.toml` é `0.1.0`. Promova para
> `## [0.1.0] - AAAA-MM-DD` e crie a tag `v0.1.0` ao cortar a primeira release.

## Camada de consumo — API + MCP (2026-05-23)

> Camada de consumo (API + MCP + biblioteca) sobre o banco já ingerido.

### Adicionado

- **`cnpj_lib/`** — biblioteca compartilhada: validador de CNPJ
  alfanumérico (Módulo 11, NT Conjunta 2025.001, vigência 06/07/2026),
  formatador e tabelas de domínio RFB. Testes + Hypothesis, cobertura 100%.
- **`app/`** — API HTTP local em FastAPI sobre SQLite read-only
  (`?mode=ro`): rotas `/health`, `/periodo-atual`, `/stats`, `/cnpj/{cnpj}`,
  `/cnpj/{basico}/socios`, `/cnpj/{basico}/estabelecimentos`. Pydantic v2,
  Swagger em pt-BR.
- **`mcp_server/`** — MCP server FastMCP `cnpj-br` com 9 tools tipadas
  (`buscar_empresa`, `listar_socios`, `listar_filiais`, `vinculos_pj`,
  `cnaes_por_municipio`, `empresas_por_cnae`, `delta_mensal`, `validar_cnpj`,
  `descrever_codigo`), reusando `app.servicos`; paginação manual
  `limit/offset` + `tem_mais`.
- **`monitor/`** — observabilidade do pipeline (coletor stdlib → `status.json`,
  dashboard HTML em loopback, controle `POST /api/run` e `/api/stop`).
- **`migrations/`** — SQL idempotente com `ANALYZE` + 4 índices.
- Suíte de testes: integração da API + MCP; fixtures em `tests/conftest.py`.
- `pyproject.toml` com extras `[api]`, `[mcp]`, `[dev]`; entrypoints `cnpj-api`
  e `mcp-cnpj`; gestão via `uv`.

## Pipeline WebDAV (2026-05-22)

### Alterado

- **Substituído o scraper Selenium por um fetcher WebDAV** do share público
  Nextcloud da RFB (`fetcher.py`: PROPFIND + GET com `Range`/retry + streaming
  1 MB). POCs Selenium preservadas na branch `experiments/spa-scraping`.
- Projeto renomeado para `dados-abertos-cnpj` (antes `dados_aberto_cpnj` —
  kebab-case + correção de typo).
- README reescrito refletindo a arquitetura WebDAV.

### Adicionado

- Smoke test do pipeline (`fetcher → database`).

## Baseline — 2024-01-07

### Adicionado

- Criação do projeto: orquestrador de download dos Dados Abertos do CNPJ,
  ingestão por streaming em SQLite local com idempotência via
  `controle_importacao` (`INSERT OR REPLACE`), log em arquivo e notificações
  opcionais Discord/Telegram (`notifier.py`).
