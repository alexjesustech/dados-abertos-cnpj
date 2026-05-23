# `monitor/` — Observabilidade do pipeline `dados-abertos-cnpj`

Conjunto leve de scripts em Python (stdlib only) + bash para acompanhar em tempo real a execução do pipeline de ingestão dos Dados Abertos do CNPJ. Tudo aqui é **somente leitura** sobre o pipeline: nenhum script desta pasta toca em `main.py`, `fetcher.py` ou `database.py`.

---

## O que ele faz

1. **Coletor (`collect.py`)** lê o `dados-abertos-cnpj.log` incrementalmente, parseia eventos conforme [`STATUS_SCHEMA.md`](./STATUS_SCHEMA.md) e mantém um snapshot vivo em `status.json`.
2. **Viewer de terminal (`status.sh`)** transforma o `status.json` em um resumo Markdown colorido.
3. **Dashboard HTML** (`dashboard.html`, mantido em paralelo por outro agente) consome o mesmo `status.json` e renderiza visão rica no browser.
4. **Notificação (`notify.sh`)** dispara `notify-send` no desktop assim que o pipeline termina (sucesso ou falha) — disparada uma única vez por run, com idempotência via `notify.sent`.

---

## Como iniciar

```bash
cd ~/projects/dados-abertos-cnpj/monitor
./start.sh
```

`start.sh` sobe o `collect.py` com `nohup`, grava o PID em `.collect.pid` e redireciona stderr para `collect.log`. Argumentos extras passados pra `start.sh` chegam ao `collect.py` (p.ex. `./start.sh --interval 2`).

Para parar:

```bash
./stop.sh
```

---

## Acompanhar o status

### No terminal (uma vez)

```bash
./status.sh
```

### No terminal (atualizando a cada 5s)

```bash
watch -n 5 ./status.sh
```

### No browser

`start.sh` sobe junto um HTTP server local (`python -m http.server`, loopback) porque o Chromium moderno bloqueia `fetch()` de arquivos sobre `file://` (CORS). Acesse:

```
http://127.0.0.1:8765/dashboard.html
```

Atalho: `xdg-open http://127.0.0.1:8765/dashboard.html`.

Configurável via env antes do `start.sh`:

- `MONITOR_HTTP_PORT` (default `8765`)
- `MONITOR_HTTP_BIND` (default `127.0.0.1`; troque para `0.0.0.0` se quiser expor na LAN — não recomendado, o dashboard não tem auth)

**Tema:** o botão ☀️/🌙 no canto superior direito alterna entre escuro (default) e claro. A escolha é persistida em `localStorage` (`monitor-theme`) e aplicada antes do primeiro render pra evitar flash.

**Controle do pipeline pelo dashboard:** ao lado do toggle de tema há um botão que muda conforme o estado:

- **▶ Executar pipeline** (verde) — visível quando não há pipeline vivo. Dispara `main.py` com os defaults do `.env` (período mais recente, `DELETE_ZIP_AFTER` como configurado, etc.). Equivale ao mesmo `nohup .venv/bin/python -u main.py > run.out 2>&1 &` que você rodaria manualmente.
- **■ Parar** (vermelho) — visível quando há pipeline vivo. Pede confirmação e manda `SIGTERM` no PID corrente.

Os botões falam com endpoints do `server.py`:

| Endpoint | Verbo | Resposta |
|---|---|---|
| `/api/run` | POST | `200 {ok:true, pid, message}` se iniciou; `409 {ok:false, error, pid}` se já há um vivo |
| `/api/stop` | POST | `200 {ok:true, pid, message}` se enviou SIGTERM; `404` se não havia ninguém pra parar |

> ⚠️ `server.py` faz bind só em `127.0.0.1` por default e não tem auth. Se você expor via `MONITOR_HTTP_BIND=0.0.0.0`, qualquer um na LAN poderá disparar/matar o pipeline — não recomendado.

---

## Como o `status.json` é populado

Schema completo (versão 1) está em [`STATUS_SCHEMA.md`](./STATUS_SCHEMA.md). Não duplicamos aqui.

Pontos-chave:

- O coletor lê o log incrementalmente, lembrando da última offset em `.collect.offset`.
- Escreve `status.json` atomicamente (`.status.json.tmp` + `os.replace`) a cada tick (default 5s) — o dashboard pode ler a qualquer instante sem ver arquivo parcial.
- Detecta término por morte do PID (`os.kill(pid, 0)`) e pela linha `Processamento e ingestão concluídos com sucesso.`.
- Após estado terminal, continua rodando por mais 60s (configurável via `--linger-seconds`) para capturar últimos eventos do log.

---

## Como reconstruir o estado do zero

`start.sh` já apaga `.collect.offset` no boot (reparse íntegro do log a cada (re)start). Se precisar zerar a flag de notificação também:

```bash
./stop.sh
rm -f notify.sent
./start.sh
```

Para um único snapshot ad hoc reconstruído do log inteiro (sem subir daemon):

```bash
rm -f .collect.offset
python collect.py --once
```

---

## Configuração de notificação

### Desktop (Ubuntu/Linux)

`notify.sh` usa `notify-send` (pacote `libnotify-bin`):

```bash
sudo apt install libnotify-bin
```

Sem `notify-send` no PATH, o script registra um aviso em `notifications.log` mas não falha — o pipeline e o coletor seguem normalmente.

Todas as notificações são também logadas em `monitor/notifications.log` no formato:

```
[2026-05-23T05:42:11-03:00] completed: Período 2026-05 concluído — 37/37 ZIPs, 37 ingestões, 0 erros.
```

### Discord / Telegram (opcional, hook futuro)

`notify.sh` já contém um placeholder comentado para webhooks Discord e Telegram. Para ativar:

1. Descomente o bloco no final do arquivo.
2. Exporte as envs antes de subir o coletor (ou coloque em `~/.zshrc`):
   ```bash
   export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/.../..."
   export TELEGRAM_BOT_TOKEN="..."
   export TELEGRAM_CHAT_ID="..."
   ```

---

## Layout de arquivos

```
monitor/
├── README.md                ← este arquivo
├── STATUS_SCHEMA.md         ← contrato JSON (versionado)
├── collect.py               ← coletor (daemon, stdlib only)
├── server.py                ← HTTP server (stdlib): estáticos + /api/run + /api/stop
├── notify.sh                ← dispara notify-send + append em notifications.log
├── status.sh                ← viewer de terminal (bash + jq)
├── start.sh                 ← launcher (sobe coletor + server.py)
├── stop.sh                  ← encerra coletor + server.py
├── status.json              ← snapshot vivo (sobrescrito a cada tick)
├── notifications.log        ← histórico de notificações disparadas
├── collect.log              ← stderr do coletor (gerado por start.sh)
├── .collect.pid             ← lockfile do coletor (gerado por start.sh)
├── .collect.offset          ← última offset lida do log (start.sh apaga no boot)
├── .http-server.pid         ← lockfile do http.server (gerado por start.sh)
├── .http-server.log         ← stdout/stderr do http.server
└── notify.sent              ← flag de idempotência da notificação final
```

---

## Bandeiras úteis do `collect.py`

| Flag | Default | Descrição |
|---|---|---|
| `--pid N` | auto (`pgrep -f "python.*main.py"`) | PID explícito do orquestrador. |
| `--interval S` | `5.0` | Intervalo entre ticks (segundos). |
| `--once` | — | Roda um único tick e sai (rebuild manual). |
| `--log PATH` | `../dados-abertos-cnpj.log` | Caminho do log estruturado. |
| `--run-out PATH` | `../run.out` | Caminho do stdout/stderr do pipeline. |
| `--status PATH` | `./status.json` | Caminho de saída. |
| `--linger-seconds N` | `60` | Quanto tempo manter ativo após estado terminal. |

---

## Princípios

- **Stdlib only.** Coletor não pode adicionar dependências ao projeto.
- **Não invasivo.** Só lê arquivos do pipeline (`log`, `run.out`) e o PID.
- **Robusto.** Linha do log que não bate em nenhum padrão é ignorada silenciosamente; `status.json` corrompido força rebuild.
- **Idempotente.** Apagar `.collect.offset` reconstrói o estado integralmente.
- **Atômico.** Toda escrita em `status.json` é via `tmp` + `os.replace`.
