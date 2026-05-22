# dados-abertos-cnpj — Diretrizes para Agentes de IA

Este arquivo define **como agentes de IA** (Gemini Antigravity, Claude Code, etc.) devem se comportar dentro deste projeto. A arquitetura técnica completa fica em [`CLAUDE.md`](./CLAUDE.md); não duplique aqui.

---

## 🌐 Idioma

* **Português do Brasil** em tudo que persiste: documentação técnica, comentários de código, mensagens de commit, mensagens de log, strings exibidas ao usuário, frontmatter de YAML.
* Inglês só em identificadores (nomes de função/variável/coluna) e termos técnicos sem tradução natural (`streaming`, `chunk`, `PROPFIND`).

---

## ✍️ Convenções de Código

* Estilo geral: PEP 8 com regras de `.pylintrc`.
* Strings de log em PT-BR. Severidades via `logging.INFO/WARNING/ERROR` repassadas ao `Notifier.log_and_notify(message, level=...)`.
* **Sem `print()` direto** em código de produção — usar sempre o `Notifier` (que loga em arquivo + opcionalmente notifica Discord/Telegram).
* Comentários só onde o porquê não for óbvio do código; evitar comentários narrativos.
* Path resolution: usar `pathlib.Path`, não `os.path.join`.

---

## 🤖 Como agir neste repo

* **Antes de propor mudança arquitetural**, leia `CLAUDE.md` para entender a divisão `main → fetcher → database → notifier`. Mantenha essa separação.
* **Antes de adicionar dependência**, avalie se dá pra resolver com stdlib. O projeto hoje tem apenas `requests` justamente para manter a árvore enxuta.
* **Antes de alterar schema do SQLite**, verifique a tabela `controle_importacao` — mudanças DDL precisam considerar bancos já populados em produção.
* **Antes de tocar no `fetcher.py`**, lembre: a fonte é um share público de Nextcloud da RFB. Se o `RFB_SHARE_TOKEN` ou o path mudar, é só configuração — não reescreva pra usar Selenium ou outra fonte.

---

## ✅ Checklist antes de commitar

1. Rodou `pylint *.py` sem regressões.
2. Mensagens novas de log estão em PT-BR.
3. Strings sensíveis (token, webhook, paths absolutos do usuário) **não** entraram no diff.
4. Se mexeu em DDL, atualizou o trecho correspondente em `CLAUDE.md`.
5. Mensagem de commit em PT-BR, imperativo (`adiciona X`, `corrige Y`, `remove Z`).

---

## 🚫 Não faça

* Não reintroduza Selenium, geckodriver ou drivers de navegador — a fonte é HTTP estático via WebDAV.
* Não baixe o CSV para disco antes de ingerir — o pipeline já faz streaming direto do ZIP. Reverter isso recupera ~50 GB de pico de disco como custo.
* Não troque `INSERT OR REPLACE` por `INSERT` puro nas tabelas com PK — quebra idempotência em re-execuções parciais.
* Não hardcode o token do share no código — sempre via `RFB_SHARE_TOKEN` (com default em `fetcher.py` apenas como fallback).
