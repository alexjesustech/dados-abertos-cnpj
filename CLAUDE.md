# dados_aberto_cpnj — Pipeline de Ingestão CNPJ

Pipeline Python que baixa os Dados Abertos do CNPJ (Receita Federal) via WebDAV público do Nextcloud da RFB e ingere em SQLite local, com retomada e idempotência.

---

## 🛠️ Comandos Frequentes

* **Ativar venv**: `source .venv/bin/activate`
* **Executar o pipeline completo**: `.venv/bin/python main.py`
* **Instalar dependências**: `.venv/bin/pip install -r requirements.txt`
* **Análise estática**: `.venv/bin/pylint *.py` (config em `.pylintrc`)

---

## 🏗️ Arquitetura

Três módulos de produção, todos em PT-BR:

* **`main.py`** — Orquestrador. Carrega `.env`, recria `temp/`, instancia `Notifier`, chama `CNPJFetcher.fetch_all()` e em seguida `DatabaseManager` (init → import por ZIP → índices).

* **`fetcher.py`** — Cliente WebDAV público do Nextcloud da RFB.
  * Base: `https://arquivos.receitafederal.gov.br/public.php/webdav/`
  * Auth: `(RFB_SHARE_TOKEN, "")` — token do share público (padrão `gn672Ad4CF8N6TK`)
  * Path CNPJ: `Dados/Cadastros/CNPJ/<YYYY-MM>/`
  * `latest_period()` faz PROPFIND em `Dados/Cadastros/CNPJ/` e retorna o maior `YYYY-MM` lexicográfico
  * `download_zip()` valida via `Content-Length`, retoma parciais via `Range: bytes=N-` com retry exponencial (até 5 tentativas), streaming em chunks de 1 MB

* **`database.py`** — SQLite. Schemas DDL para `empresas`, `estabelecimentos`, `socios`, `simples`, `cnaes`, `motivos`, `municipios`, `paises`, `qualificacoes`, `naturezas`. Ingestão por streaming direto do ZIP via `zipfile.ZipFile.open()` + `io.TextIOWrapper` (sem extração em disco), commits a cada 50k linhas, PRAGMAs agressivos (`synchronous=OFF`, `journal_mode=WAL`, `cache_size=100000`, `temp_store=MEMORY`). Idempotência via tabela `controle_importacao` (`is_file_imported`/`mark_file_as_imported`). `INSERT OR REPLACE` permite re-execução parcial sem violar PKs.

* **`notifier.py`** — Logging para `dados_aberto_cpnj.log` + envio opcional para Discord Webhook e Telegram Bot. Carrega `.env` via parser próprio (sem dependência de `python-dotenv`).

⚠️ **PRAGMAs agressivos**: `synchronous=OFF` torna o banco vulnerável a corrupção em crash de OS (não de processo). Aceitável aqui porque o pipeline é re-executável e a tabela `controle_importacao` permite retomar.

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
        "/home/sander/projects/dados_aberto_cpnj/dados_cnpj.db"
      ]
    }
  }
}
```

---

## 🔄 Operação e Retomada

* O run cria/reseta `temp/` no início — arquivos parciais do run anterior **não** são preservados entre execuções (resume é por-arquivo dentro do mesmo run, via `Range`).
* Ingestão é idempotente: ZIPs já registrados em `controle_importacao` são pulados. Para reprocessar, `DELETE FROM controle_importacao WHERE arquivo = 'X.zip'`.
* Logs em `dados_aberto_cpnj.log` (ignorado pelo git).
* Notificações via Discord/Telegram são opcionais — controladas só pela presença das envs.

---

## 🗂️ Volumes Esperados

Período `2026-05` (referência):
* 37 ZIPs, ~8 GB comprimidos
* `Estabelecimentos0.zip` é o maior individual (~2 GB)
* Banco final descomprimido: ~50 GB
