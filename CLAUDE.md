# dados-abertos-cnpj — Pipeline + API + MCP server

Pipeline Python que baixa os Dados Abertos do CNPJ (Receita Federal) via WebDAV público do Nextcloud da RFB e ingere em SQLite local, com retomada e idempotência. Sobre esse banco vivem **dois consumidores**: uma **API HTTP local** (FastAPI) e um **MCP server** (FastMCP, 9 tools) — ambos read-only, em pt-BR.

## 📚 Série de documentos

Três peças encadeadas em `docs/` registram a decisão e a execução do Caminho 01 ("Caixa-preta de CNPJ pra mim"):

| Nº | Documento | Tipo |
|---|---|---|
| 001 | [`briefing-2026-05-23.html`](./docs/briefing-2026-05-23.html) | Pesquisa de viabilidade (mercado + restrições legais + 10 soluções + 3 caminhos) |
| 002 | [`briefing-implementacao-2026-05-23.html`](./docs/briefing-implementacao-2026-05-23.html) | Plano executável (stack + estrutura + 4 sprints + modelagem JSON) |
| 003 | [`relatorio-execucao-2026-05-23.html`](./docs/relatorio-execucao-2026-05-23.html) | Relatório de entrega (4 sprints concluídos + métricas + decisões registradas) |

Sistema visual: [`docs/design/dossie-editorial.md`](./docs/design/dossie-editorial.md) — variante B (creme + Newsreader + vermillion único, sem emoji).

---

## 🛠️ Comandos Frequentes

### Pipeline (camada original)

* **Executar o pipeline completo**: `.venv/bin/python main.py`
* **Instalar dependências (legado)**: `.venv/bin/pip install -r requirements.txt`
* **Análise estática**: `.venv/bin/pylint *.py`

### API + MCP (Caminho 01)

* **Setup uv**: `uv sync --extra api --extra mcp --extra dev`
* **Levantar API**: `uv run cnpj-api` → `http://127.0.0.1:8000` (Swagger em `/docs`)
* **Levantar MCP stdio**: `uv run mcp-cnpj` (geralmente chamado pelo Claude Code via `~/.claude/mcp.json`)
* **Rodar testes**: `uv run pytest tests/ -v` (60 unitários, cobertura 100% em `cnpj_lib/`)
* **Lint moderno**: `uv run ruff check .`

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
tests/unit/              60 testes pytest + Hypothesis, cobertura 100% em cnpj_lib/
tests/integracao/        (vazio — backlog)
tests/mcp/               (vazio — backlog)
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
