# dados-abertos-cnpj — Pipeline + API + MCP server

Pipeline Python que baixa os Dados Abertos do CNPJ (Receita Federal) via WebDAV público do Nextcloud da RFB e ingere em SQLite local, com retomada e idempotência. Sobre esse banco vivem **dois consumidores**: uma **API HTTP local** (FastAPI) e um **MCP server** (FastMCP, 9 tools) — ambos read-only, em pt-BR.

> **📍 Estado em 2026-05-23 (pausa)** — pipeline executado (banco com 37 GB, período `2026-05`), monitor + API integ + MCP tests no commits `a7b4693`/`d2707c2`/`45496e2`/`origin/main`. **WIP não commitado:** suite `tests/mcp/` (4 arquivos + conftest, 37 testes verde) + refator de `tests/conftest.py` (compartilha `tmp_db_path`/`cnpjs`) — `git status` mostra o set. Próximo passo: split em 2 commits (refactor + test) e push.

## 📚 Série de documentos

Três peças encadeadas em `docs/` registram a decisão e a execução do Caminho 01 ("Caixa-preta de CNPJ pra mim"):

| Nº | Documento | Tipo |
|---|---|---|
| 001 | [`briefing-2026-05-23.html`](./docs/briefing-2026-05-23.html) | Pesquisa de viabilidade (mercado + restrições legais + 10 soluções + 3 caminhos) |
| 002 | [`briefing-implementacao-2026-05-23.html`](./docs/briefing-implementacao-2026-05-23.html) | Plano executável (stack + estrutura + 4 sprints + modelagem JSON) |
| 003 | [`relatorio-execucao-2026-05-23.html`](./docs/relatorio-execucao-2026-05-23.html) | Relatório de entrega (4 sprints concluídos + métricas + decisões registradas) |
| 004 | [`backlog-2026-05-23.html`](./docs/backlog-2026-05-23.html) | Backlog &amp; alternativas pós-pausa (estado, polimento, caminhos 02/03, 10 soluções, decisões válidas) |

Sistema visual: [`docs/design/dossie-editorial.md`](./docs/design/dossie-editorial.md) — variante B (creme + Newsreader + vermillion único, sem emoji).

---

## 🤖 Diretrizes para Agentes de IA

Este projeto é lido tanto pelo Claude Code quanto por agentes Gemini (Antigravity, Code Assist, CLI) — ambos consomem este mesmo arquivo via symlink `GEMINI.md → CLAUDE.md`, conforme política global em [`../CLAUDE.md`](../CLAUDE.md). Regras específicas deste repo (consolidadas do antigo `GEMINI.md` em 2026-05-25):

### Convenções de código

* PEP 8 + regras de `.pylintrc`. Comentários só onde o porquê não for óbvio.
* **Sem `print()` direto** em código de produção — usar sempre `Notifier.log_and_notify(message, level=logging.INFO|WARNING|ERROR)`; cuida de log em arquivo + Discord/Telegram opcionais.
* Path resolution via `pathlib.Path`, **nunca** `os.path.join`.
* Strings de log em pt-BR (segue a política global do workspace).

### Antes de mudar

* **Arquitetura:** preserve a divisão `main → fetcher → database → notifier` (ver "Arquitetura" abaixo). Se for refatorar, justifique o desvio.
* **Dependências:** avaliar stdlib primeiro. A camada original tem só `requests` justamente pra manter a árvore enxuta; a camada nova (API+MCP) entra via `uv` com extras (`--extra api`, `--extra mcp`, `--extra dev`).
* **Schema do SQLite:** verificar `controle_importacao` — DDL muda comportamento em bancos já populados em produção.
* **`fetcher.py`:** a fonte é HTTP estático via WebDAV público da RFB. Se `RFB_SHARE_TOKEN` ou path mudar, é configuração — **não** reescrever pra usar Selenium ou outra fonte (POCs antigas estão preservadas na branch `experiments/spa-scraping`).

### Checklist pré-commit

1. `pylint *.py` (camada original) e/ou `uv run ruff check .` (camada nova) sem regressões.
2. Logs novos em pt-BR.
3. Sem token, webhook ou path absoluto do usuário no diff.
4. Se mexeu em DDL, atualizou o trecho correspondente em "Arquitetura".
5. Mensagem de commit em pt-BR, imperativo (`adiciona X`, `corrige Y`, `remove Z`).

### Não faça

* **Sem Selenium / geckodriver / drivers de navegador** — a fonte é HTTP estático via WebDAV.
* **Sem baixar ZIP pra disco antes de ingerir** — o pipeline já faz streaming direto do ZIP; reverter custa ~50 GB de pico de disco.
* **Sem trocar `INSERT OR REPLACE` por `INSERT` puro** em tabelas com PK — quebra idempotência em re-execuções parciais.
* **Sem hardcode do `RFB_SHARE_TOKEN`** no código — sempre via env (o default em `fetcher.py` é só fallback).

---

## 🛠️ Comandos Frequentes

> Comandos que leem envs (DB_PATH, TELEGRAM_BOT_TOKEN, etc.) devem ser prefixados por `bin/with-env` desde a migração SOPS+age de 2026-05-24 — vide seção "Segredos" no final deste documento.

### Pipeline (camada original)

* **Executar o pipeline completo**: `bin/with-env .venv/bin/python main.py`
* **Instalar dependências (legado)**: `.venv/bin/pip install -r requirements.txt`
* **Análise estática**: `.venv/bin/pylint *.py`

### API + MCP (Caminho 01)

* **Setup uv**: `uv sync --extra api --extra mcp --extra dev`
* **Levantar API**: `bin/with-env uv run cnpj-api` → `http://127.0.0.1:8000` (Swagger em `/docs`)
* **Levantar MCP stdio**: `bin/with-env uv run mcp-cnpj` (geralmente chamado pelo Claude Code via `~/.claude/mcp.json`)
* **Rodar testes**: `bin/with-env uv run pytest tests/ -v` (60 unitários, cobertura 100% em `cnpj_lib/`)
* **Lint moderno**: `uv run ruff check .`

### Monitor (observabilidade do pipeline)

* **Subir coletor + dashboard**: `monitor/start.sh` (loopback `http://127.0.0.1:8765/dashboard.html`)
* **Parar**: `monitor/stop.sh`
* **Status no terminal**: `monitor/status.sh` (ou `watch -n 5 monitor/status.sh`)
* **Configuração opcional**: `MONITOR_HTTP_PORT` (default `8765`), `MONITOR_HTTP_BIND` (default `127.0.0.1` — não expor na LAN, dashboard sem auth)

---

## 🏗️ Arquitetura

### Camada original — Pipeline de ingestão

Quatro módulos em PT-BR na raiz do repo:

* **`main.py`** — Orquestrador. Carrega `.env`, recria `temp/`, instancia `Notifier`, chama `CNPJFetcher.fetch_all()` e em seguida `DatabaseManager` (init → import por ZIP → índices).
* **`fetcher.py`** — Cliente WebDAV público do Nextcloud da RFB. Base `https://arquivos.receitafederal.gov.br/public.php/webdav/`; auth `(RFB_SHARE_TOKEN, "")`; `latest_period()` via PROPFIND; `download_zip()` com `Range:` + retry exponencial + streaming 1 MB.
* **`database.py`** — SQLite. Schemas DDL das 10 tabelas (`empresas`, `estabelecimentos`, `socios`, `simples` + 6 lookups). Ingestão por streaming do ZIP (`zipfile.ZipFile.open()` + `io.TextIOWrapper`); commits a cada 50k linhas; PRAGMAs agressivos. Idempotência via `controle_importacao` + `INSERT OR REPLACE`.
* **`notifier.py`** — Log + Discord/Telegram opcionais. Parser próprio de `.env`.

⚠️ **`synchronous=OFF`** torna o banco vulnerável a crash de OS (não de processo). Aceitável: pipeline é re-executável.

### Camada nova — API + MCP (Caminho 01, 2026-05-23)

```
cnpj_lib/                Biblioteca compartilhada (J — validador alfanumérico)
├── validador.py         Módulo 11 (alfa + num) — NT Conjunta 2025.001, vigência 06/07/2026
├── formatador.py        normalizar · formatar · fragmentar · mascarar_cpf · parsear_data
└── dominio.py           6 tabelas hardcoded RFB (situacao_cadastral, etc) + descrever()

app/                     Núcleo da API HTTP (A) — reusado pelo MCP
├── main.py              FastAPI + lifespan + run_uvicorn()
├── config.py            pydantic-settings (DB_PATH, API_BIND, API_PORT, CORS_ORIGINS)
├── db.py                sqlite3 URI ?mode=ro (read-only por design)
├── dependencias.py      Depends(conn) + validação de CNPJ no path (422 se inválido)
├── schemas/             Pydantic v2 — compartilhado com MCP
├── repositorios/        SQL puro (empresa, estabelecimento, socio, lookup, busca, controle)
├── servicos/            consulta_cnpj.montar_cnpj_completo — orquestrador único
└── rotas/               /health · /periodo-atual · /stats · /cnpj/{cnpj} + subrotas

mcp_server/              Servidor MCP (I)
└── server.py            FastMCP("cnpj-br") + 9 tools tipadas via @mcp.tool()

migrations/              SQL idempotente (ANALYZE + 4 índices novos aplicados 2026-05-23)
tests/conftest.py        Fixtures compartilhadas: tmp_db_path + cnpjs (WIP, 2026-05-23)
tests/unit/              60 testes pytest + Hypothesis, cobertura 100% em cnpj_lib/
tests/integracao/        27 testes — FastAPI TestClient contra SQLite descartável (commit 45496e2)
tests/mcp/               37 testes — chamada direta das 9 tools FastMCP (WIP, 2026-05-23)

monitor/                 Observabilidade — stdlib only, não invasivo
├── collect.py           Daemon que parseia dados-abertos-cnpj.log → status.json
├── server.py            HTTP server (loopback) + POST /api/run + POST /api/stop
├── dashboard.html       SPA Tailwind + Alpine consumindo status.json
├── status.sh            Viewer Markdown colorido pro terminal
├── notify.sh            notify-send local + placeholders Discord/Telegram
├── start.sh · stop.sh   Lockfiles em monitor/.collect.pid e .http-server.pid
└── STATUS_SCHEMA.md     Contrato versionado do status.json (schema_version=1)
```

**As 9 tools do MCP**: `buscar_empresa`, `listar_socios`, `listar_filiais`, `vinculos_pj`, `cnaes_por_municipio`, `empresas_por_cnae`, `delta_mensal` (MVP), `validar_cnpj`, `descrever_codigo`. Todas paginadas manualmente com `limit/offset` + `tem_mais` (MCP não tem paginação nativa para `tools/call`).

**Pontos de reuso**: o MCP importa apenas `app.servicos` — nunca `app.rotas` — para não inflar startup com FastAPI. API e MCP compartilham os mesmos models Pydantic em `app/schemas/`.

---

## ⚙️ Configuração (`.env`)

| Variável | Padrão | Função |
|---|---|---|
| `DB_PATH` | `dados_cnpj.db` | Caminho do SQLite |
| `DELETE_ZIP_AFTER` | `false` | Apaga ZIP após ingestão OK |
| `RFB_SHARE_TOKEN` | `gn672Ad4CF8N6TK` | Token do share Nextcloud — atualizar se a RFB rotacionar |
| `CNPJ_PERIOD` | _(vazio)_ | Força período `YYYY-MM`. Vazio = último disponível |
| `DISCORD_WEBHOOK_URL` | _(vazio)_ | Notificações Discord |
| `TELEGRAM_BOT_TOKEN` | _(vazio)_ | Token do bot Telegram |
| `TELEGRAM_CHAT_ID` | _(vazio)_ | Chat-alvo do Telegram |

---

## 📦 Dependências

Apenas `requests==2.31.0`. Toda lógica de WebDAV é manual via PROPFIND/GET com headers HTTP padrão.

---

## 📊 Integração com MCP SQLite

Para consultas ad hoc no banco já ingerido, registre o servidor SQLite MCP em `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "sqlite-cnpj": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite",
        "--db",
        "/home/sander/projects/dados-abertos-cnpj/dados_cnpj.db"
      ]
    }
  }
}
```

---

## 🔄 Operação e Retomada

* O run cria/reseta `temp/` no início — arquivos parciais do run anterior **não** são preservados entre execuções (resume é por-arquivo dentro do mesmo run, via `Range`).
* Ingestão é idempotente: ZIPs já registrados em `controle_importacao` são pulados. Para reprocessar, `DELETE FROM controle_importacao WHERE arquivo = 'X.zip'`.
* Logs em `dados-abertos-cnpj.log` (ignorado pelo git).
* Notificações via Discord/Telegram são opcionais — controladas só pela presença das envs.

---

## 🗂️ Volumes Esperados

Período `2026-05` (referência):
* 37 ZIPs, ~8 GB comprimidos
* `Estabelecimentos0.zip` é o maior individual (~2 GB)
* Banco final descomprimido: ~50 GB


---

## Segredos

Migrado para **SOPS + age** em 2026-05-24 (substitui o `.env` plaintext legado). Stack do projeto:

| Item | Onde | Notas |
|---|---|---|
| `.env.sops.yaml` | raiz do repo, **versionado** | Ciphertext. Cifrado pra public key age `age17utcae5zrq0qfhaundd7u7wa74nm54a597pjg7q2ukl8s8883f9srky767` (workstation `base-station`). |
| `.sops.yaml` | raiz do repo, versionado | Config file: declara o recipient age pro `creation_rules`. Evita ter que passar `--age` em cada operação. |
| `.env` plaintext | `~/projects/dados-abertos-cnpj/.env`, **gitignored** | Mantido localmente como fallback (pydantic_settings lê do arquivo OU do env — env vence). **Deve ser shredded** após validação total. |
| `bin/with-env` | versionado, +x | Wrapper que injeta vars do `.env.sops.yaml` no subprocess via `sops exec-env`. Vars **não vazam** pro env do shell pai. |

### Como rodar comandos que precisam de envs

Prefixar comandos com `bin/with-env`:

```bash
bin/with-env .venv/bin/python main.py
bin/with-env uv run cnpj-api
bin/with-env uv run mcp-cnpj
bin/with-env uv run pytest tests/ -v
```

### Como editar valores

```bash
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt EDITOR=micro sops .env.sops.yaml
```

(Editor `micro` é o default da workstation — substituir por `nano`/`vim`/`code -w` se preferir.)

**NUNCA editar `.env.sops.yaml` direto via `micro .env.sops.yaml`** — quebra o MAC e o arquivo vira inválido. Howto canônico (humanos + agentes): [`../docs/sops-secrets-howto.md`](../docs/sops-secrets-howto.md). Política global: [`../CLAUDE.md`](../CLAUDE.md) "Segredos & envs (SOPS + age)".
