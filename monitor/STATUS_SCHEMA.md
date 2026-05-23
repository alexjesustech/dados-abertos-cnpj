# Contrato: `monitor/status.json`

Arquivo único que o **coletor** escreve e o **dashboard** lê. Schema versionado (`schema_version`) — qualquer mudança incompatível precisa bumpar a versão e atualizar ambos os lados.

## Schema (versão 1)

```jsonc
{
  "schema_version": 1,

  // Identificação do processo
  "pid": 72665,                    // PID do `main.py`
  "alive": true,                   // processo ainda existe?

  // Estado macro
  "state": "running",              // "running" | "completed" | "failed"
  "started_at": "2026-05-23T01:34:27-03:00",   // ISO 8601 com offset local
  "last_event_at": "2026-05-23T01:35:12-03:00",
  "ended_at": null,                // preenchido quando state ∈ {completed, failed}

  // Contexto do run
  "period": "2026-05",             // YYYY-MM identificado pelo fetcher
  "total_zips": 37,                // total esperado de ZIPs no período
  "total_bytes": 7530000000,       // soma dos sizes anunciados pelo WebDAV (do log: "~7.01 GB")

  // Eventos discretos (append-only; coletor adiciona, nunca remove)
  "downloads": [
    {
      "name": "Cnaes.zip",
      "expected_bytes": 22078,
      "status": "done",            // "in_progress" | "done" | "failed"
      "started_at": "2026-05-23T01:34:28-03:00",
      "completed_at": "2026-05-23T01:34:28-03:00",
      "attempts": 1,               // total de tentativas (>=1)
      "resumed": false             // true se houve algum [resume] pra esse arquivo
    }
  ],
  "ingestions": [
    {
      "zip": "Cnaes.zip",
      "table": "cnaes",
      "rows": 1359,
      "duration_seconds": 0.00,
      "status": "ok",              // "ok" | "failed"
      "completed_at": "2026-05-23T01:34:30-03:00"
    }
  ],
  "errors": [
    {
      "ts": "2026-05-23T01:40:00-03:00",
      "level": "WARNING",          // do logging do notifier (WARNING/ERROR)
      "message": "[warn] Empresas0.zip: tamanho final X != esperado Y."
    }
  ],

  // Snapshot derivado (recalculado a cada tick do coletor)
  "current_action": "Baixando Empresas0.zip (502 MB)",
  "summary": {
    "downloaded_count": 1,
    "downloaded_bytes": 22078,
    "ingested_count": 1,
    "downloads_in_progress": 1,
    "errors_count": 0,
    "progress_pct": 2.5,           // baseado em downloaded_bytes + ingestões concluídas (heurística simples)
    "elapsed_seconds": 45,
    "eta_seconds": null            // null se ainda não dá pra estimar
  }
}
```

## Eventos do log que o coletor precisa reconhecer

Padrões fixos do `notifier.log_and_notify(...)`. Linha do log tem o formato:
`YYYY-MM-DD HH:MM:SS,mmm [LEVEL] mensagem`

### Marcos do orquestrador (`main.py`)
- `Início da extração e ingestão dos Dados Abertos do CNPJ.` → marca `started_at`
- `Limpando diretório temporário (...).` → ignorar (info)
- `Download concluído (N arquivos) para o período YYYY-MM.` → marca fim da fase download
- `Excluindo X.zip para liberar espaço.` → ignorar (efeito de `DELETE_ZIP_AFTER=true`)
- `Processamento e ingestão concluídos com sucesso.` → **state = "completed"**, popula `ended_at`
- `Falha no download dos ZIPs: ...` → **state = "failed"**, registra em `errors`
- `Falha na ingestão de X.zip: ...` → registra em `errors`; só vira `state="failed"` se o processo morrer

### Fetcher (`fetcher.py`)
- `Período-alvo: YYYY-MM` → popula `period`
- `N arquivos ZIP no período YYYY-MM (~X.XX GB).` → popula `total_zips` e `total_bytes` (converter GB→bytes; aceitar 2 casas)
- `[get] X.zip (N bytes, tentativa T).` → cria download com `status=in_progress`, `started_at=ts`, `attempts=T`
- `[resume] X.zip de A/B bytes (tentativa T).` → marca `resumed=true`, atualiza `attempts`
- `[skip] X.zip já presente (N bytes).` → cria download já como `status=done`
- `[warn] X.zip: tamanho final X != esperado Y.` → registra em `errors` (level WARNING)
- `[err] X.zip tentativa N/M: ...` → registra em `errors`

A conclusão de cada download é **inferida** pela linha seguinte no log:
- Se vier outro `[get]`, `[resume]` ou `[skip]` para outro nome → o anterior virou `status=done` no `ts` da nova linha.
- Se vier `Iniciando leitura por streaming do arquivo ZIP: X.zip...` antes de qualquer outro download, o anterior virou `done`.
- Se vier `Download concluído (N arquivos)`, fechar todos pendentes.

### Database (`database.py`)
- `Inicializando o banco de dados em: ...` → ignorar
- `Tabelas do banco de dados criadas/verificadas com sucesso.` → ignorar
- `Iniciando leitura por streaming do arquivo ZIP: X.zip...` → cria ingestion com `status=ok` pendente (status final só quando vier `finalizada`)
- `Importando ... (dentro de X.zip) para a tabela 'T'...` → guarda `table=T` na ingestion atual de `X.zip`
- `Tabela 'T' finalizada. Ingeridos N registros em D.DD segundos.` → fecha a ingestion: `rows=N`, `duration_seconds=D.DD`, `completed_at=ts`
- `Criando índices para otimização de consultas...` → atualiza `current_action="Criando índices"`
- `Índices criados com sucesso.` → ignorar (sucesso final virá da linha do main)

### Heurística de `current_action`
1. Se há download `in_progress` → `"Baixando X (Y MB, tentativa T)"`
2. Senão, se há ingestion sem `completed_at` → `"Ingerindo X → tabela T"`
3. Senão, se viu "Criando índices" mas não viu "Índices criados" → `"Criando índices"`
4. Senão, se state == completed → `"Concluído"`; failed → `"Falha"`
5. Senão → última linha do log, prefixada com `"…"`

### Heurística de `progress_pct`
- Peso 0.6 para download: `downloaded_bytes / total_bytes`
- Peso 0.4 para ingestão: `ingested_count / total_zips`
- Combinado: `60*download_ratio + 40*ingest_ratio`

## Detecção de término

A cada tick (5s sugerido):
1. Verificar se `pid` ainda existe (`/proc/<pid>` no Linux ou `os.kill(pid, 0)` capturando `ProcessLookupError`).
2. Se o processo morreu E não houve a linha de sucesso → `state = "failed"`, `ended_at = agora`. Adicionar em `errors` o tail das últimas N linhas do log + `run.out`.
3. Se a linha `Processamento e ingestão concluídos com sucesso.` apareceu → `state = "completed"`.
4. Em ambas transições, disparar notificação **uma única vez** (idempotência: marcar flag em arquivo separado `notify.sent`).

## Notificação

Quando state muda para `completed` ou `failed`:
1. `notify-send -u {normal|critical} "Pipeline CNPJ" "<resumo>"` (libnotify; já disponível no Ubuntu)
2. Append em `monitor/notifications.log` com timestamp + state + resumo
3. Print no stdout do coletor (caso esteja em foreground)
