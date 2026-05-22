# dados_aberto_cpnj

Pipeline em Python para baixar os **Dados Abertos do CNPJ** publicados pela Receita Federal do Brasil (RFB) e ingerir em um banco SQLite local, com retomada parcial e notificações opcionais (Discord/Telegram).

A fonte é o share público de Nextcloud da RFB em [`arquivos.receitafederal.gov.br`](https://arquivos.receitafederal.gov.br/index.php/s/gn672Ad4CF8N6TK). O pipeline detecta automaticamente o período mais recente (`YYYY-MM`) e baixa os ~37 ZIPs do mês (Empresas, Estabelecimentos, Sócios, Simples e tabelas de domínio).

## Pré-requisitos

- **Python ≥ 3.10** (testado em 3.12)
- **~10 GB livres** para os ZIPs do mês mais recente
- **~50 GB livres** para o banco SQLite final (cresce com o tempo)
- Conexão estável — o maior ZIP (`Estabelecimentos0.zip`) tem ~2 GB

## Instalação

```bash
git clone git@github.com:alexjesustech/dados_aberto_cpnj.git
cd dados_aberto_cpnj

python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate.bat       # Windows

pip install -r requirements.txt
cp .env.example .env
```

## Configuração (`.env`)

| Variável | Padrão | Função |
|---|---|---|
| `DB_PATH` | `dados_cnpj.db` | Caminho do banco SQLite |
| `DELETE_ZIP_AFTER` | `false` | Apaga cada ZIP após ingestão bem-sucedida (libera disco) |
| `RFB_SHARE_TOKEN` | `gn672Ad4CF8N6TK` | Token do share Nextcloud da RFB. Atualize se a RFB rotacionar |
| `CNPJ_PERIOD` | _(vazio)_ | Força um período `YYYY-MM` específico. Vazio = mais recente |
| `DISCORD_WEBHOOK_URL` | _(vazio)_ | Webhook do Discord para notificações |
| `TELEGRAM_BOT_TOKEN` | _(vazio)_ | Token do bot do Telegram |
| `TELEGRAM_CHAT_ID` | _(vazio)_ | Chat de destino no Telegram |

## Como rodar

```bash
.venv/bin/python main.py
```

O pipeline:

1. Consulta o share WebDAV da RFB e identifica o período `YYYY-MM` mais recente
2. Lista todos os ZIPs do período e baixa para `temp/` com retomada via HTTP `Range` (retry exponencial até 5 tentativas)
3. Inicializa as tabelas em `dados_cnpj.db` (idempotente via tabela `controle_importacao`)
4. Para cada ZIP, faz streaming do CSV interno direto pro SQLite em chunks de 50 mil linhas
5. Cria índices ao final

Logs em `dados_aberto_cpnj.log`. Notificações opcionais se as variáveis do Discord/Telegram estiverem preenchidas.

## Estrutura

```
main.py        # orquestrador (fetcher → database)
fetcher.py     # cliente WebDAV: PROPFIND + GET com Range/retry
database.py    # DDL, ingestão por streaming, índices, controle_importacao
notifier.py    # logging para arquivo + Discord/Telegram opcional
```

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---|---|---|
| `HTTP 401` no PROPFIND | Token do share rotacionado pela RFB | Acesse `https://arquivos.receitafederal.gov.br/` (redireciona pro share novo), pegue o novo token e atualize `RFB_SHARE_TOKEN` no `.env` |
| `HTTP 404` no PROPFIND | Path do CNPJ mudou no share | Inspecione o share manualmente, ajuste `CNPJ_PATH` em `fetcher.py` |
| Download trava | Conexão instável | O fetcher já tem retry com resume; deixe rodar. Pra forçar retry imediato, mate o processo e rode de novo — arquivos parciais em `temp/` são retomados via `Range` |
| Ingestão pula um ZIP | Arquivo já registrado em `controle_importacao` | Comportamento esperado (idempotência). Para reprocessar, delete a linha correspondente na tabela `controle_importacao` |
| Run anterior incompleto | Crash no meio | A tabela `controle_importacao` rastreia o que já foi ingerido; basta rodar `main.py` de novo |

## Fonte de dados

- Portal oficial: <https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj>
- Share Nextcloud (fonte real dos arquivos): <https://arquivos.receitafederal.gov.br/index.php/s/gn672Ad4CF8N6TK>
- Layout dos CSVs: ver dicionário oficial da Receita Federal (`Metadados.pdf` no próprio share)
