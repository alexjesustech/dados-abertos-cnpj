# PRD — dados-abertos-cnpj

> **v0.1.0 — draft inicial derivado da documentação existente; a refinar com
> o owner.** Consolidado a partir do `CLAUDE.md`, do `README.md`, do código
> e da série de documentos em `docs/*.html` (planejamento, briefing,
> relatório de execução, backlog). Itens marcados "(a confirmar)" precisam de
> validação.

---

## 1. Visão & Problema

Os **Dados Abertos do CNPJ** publicados pela Receita Federal do Brasil (RFB)
são distribuídos como ~37 arquivos ZIP mensais (~8 GB comprimidos, ~50 GB
descomprimidos) via um share público de Nextcloud. Consumir esses dados de
forma ágil exige um pipeline de ingestão robusto e uma camada de consulta
local — caso contrário, resta depender de APIs de terceiros com rate-limit ou
de SaaS pago.

**dados-abertos-cnpj** resolve isso com:

1. um **pipeline** que baixa a safra mais recente da RFB e a ingere em um
   **SQLite local** com retomada e idempotência;
2. uma **API HTTP local** (FastAPI) e um **MCP server** (FastMCP, 9 tools),
   ambos **read-only** sobre esse banco — um espelho local rápido, sem
   rate-limit, para uso pessoal/profissional e para acelerar agentes de IA.

É o "Caminho 01" da série de planejamento: **"Caixa-preta de CNPJ pra mim"**
(A — API local + I — MCP server + J — validador alfanumérico). Uma toolchain
de uso, não um produto público.

## 2. Objetivos

- Manter um espelho local atualizável dos Dados Abertos do CNPJ em SQLite,
  ingerido de forma idempotente e re-executável.
- Expor consulta unitária rica por CNPJ (empresa + Simples + estabelecimentos
  + QSA) resolvendo códigos RFB para descrições humanas.
- Oferecer buscas cruzadas úteis (sócios por documento, CNAEs por município,
  empresas por CNAE × município/UF).
- Disponibilizar as mesmas capacidades como ferramentas tipadas a agentes de
  IA via MCP.
- Validar e reconciliar CNPJ no formato **alfanumérico** (vigência 06/07/2026).
- Resposta de consulta unitária em tempo interativo (< 200 ms observados).

## 3. Não-objetivos

- **Não** é serviço de **score de crédito / risco** nem KYB comercial.
- **Não** usa **Selenium / drivers de navegador** — a fonte é HTTP estático via
  WebDAV; POCs Selenium ficam só em `experiments/spa-scraping`.
- **Não** faz **enriquecimento com telefone/e-mail** nem busca reversa
  perfiladora de pessoa física (zona LGPD).
- **Não** reidentifica CPF mascarado cruzando com outras bases.
- **Não** baixa o ZIP inteiro para disco antes de ingerir — streaming direto é
  requisito (evita ~50 GB de pico).
- **Não** é serviço público hospedado de alta disponibilidade — roda local,
  loopback, single-user (a confirmar se muda em caminho futuro).
- **Não** inclui, no MVP, diff real entre safras nem grafo societário (backlog
  Caminho 02).

## 4. Personas / usuários

- **Desenvolvedor/owner (uso pessoal e profissional)** — consulta CNPJs, cruza
  CNAE × município, valida documentos; valoriza ausência de rate-limit.
- **Agente de IA (Claude Code / Gemini)** — consome as 9 tools MCP tipadas.
- **Operador do pipeline** — executa/monitora a ingestão mensal via dashboard.
- **Contexto institucional regional (Rondônia)** — usuário potencial de
  recortes regionais; caminho futuro, não escopo atual (a confirmar).

## 5. Requisitos funcionais

### 5.1 Pipeline de ingestão
- **RF-01** Detectar o período `YYYY-MM` mais recente via PROPFIND (ou forçar
  via `CNPJ_PERIOD`).
- **RF-02** Baixar os ~37 ZIPs para `temp/` com retomada via HTTP `Range` +
  retry exponencial.
- **RF-03** Streaming do CSV interno direto para o SQLite em chunks de 50 mil
  linhas (sem extrair para disco).
- **RF-04** Inicializar 10 tabelas + criar índices ao final.
- **RF-05** Idempotência via `controle_importacao`; reprocessamento por
  `DELETE` da linha.
- **RF-06** Notificações opcionais (Discord/Telegram) controladas pelas envs;
  log via `Notifier.log_and_notify`.

### 5.2 API HTTP local (FastAPI, read-only)
- **RF-07** `GET /health`.
- **RF-08** `GET /periodo-atual`.
- **RF-09** `GET /stats` (cache lazy).
- **RF-10** `GET /cnpj/{cnpj}` — dados completos; 404/422.
- **RF-11** `GET /cnpj/{basico}/socios` — paginado.
- **RF-12** `GET /cnpj/{basico}/estabelecimentos` — paginado.
- **RF-13** Swagger/OpenAPI em pt-BR em `/docs`.

### 5.3 MCP server (FastMCP `cnpj-br`, 9 tools)
- **RF-14..22** `buscar_empresa`, `listar_socios`, `listar_filiais`,
  `vinculos_pj`, `cnaes_por_municipio`, `empresas_por_cnae`, `delta_mensal`
  (MVP: só metadados), `validar_cnpj`, `descrever_codigo`.
- **RF-23** Todas as tools de listagem são paginadas manualmente
  (`limit/offset` + `tem_mais`).

### 5.4 Observabilidade (monitor)
- **RF-24** Coletor stdlib → `status.json` (schema versionado).
- **RF-25** Dashboard HTML em loopback + controle remoto; viewer Markdown.

## 6. Requisitos não-funcionais

- **RNF-01 Read-only por design** — API e MCP abrem o SQLite em `?mode=ro`.
- **RNF-02 Idempotência** — re-execução barata e segura.
- **RNF-03 Streaming sem disco** — ZIPs ingeridos por streaming.
- **RNF-04 Latência** — consulta unitária interativa (< 200 ms).
- **RNF-05 Árvore enxuta** — pipeline depende só de `requests`; camada nova via
  `uv` com extras opt-in.
- **RNF-06 Segurança/segredos** — SOPS + age (`.env.sops.yaml` + `bin/with-env`);
  sem hardcode de `RFB_SHARE_TOKEN`/webhooks/paths; pre-commit `gitleaks`.
- **RNF-07 Exposição** — monitor e API em loopback (`127.0.0.1`).
- **RNF-08 Qualidade** — gate de CI local (3 camadas estilo `nous`); `ruff` +
  `pylint` sem regressões.
- **RNF-09 Idioma** — logs, docs e commits em pt-BR.
- **RNF-10 Conformidade LGPD** — faixa "verde" (redistribuição com atribuição,
  agregados); CPF apenas mascarado; evitar busca reversa perfiladora.

## 7. Critérios de aceite

- **CA-01** Pipeline ingere a safra mais recente num SQLite local, re-executável
  sem duplicar. *(Atendido — banco ~37 GB, período `2026-05`.)*
- **CA-02** `GET /cnpj/{cnpj}` retorna empresa + QSA + estabelecimentos
  resolvidos, em tempo interativo. *(Atendido.)*
- **CA-03** As 9 tools MCP respondem corretamente sobre os dados de produção.
  *(Tools entregues; validação visual no cliente marcada como pendente.)*
- **CA-04** Validador aceita CNPJ numérico e alfanumérico (cobertura 100% em
  `cnpj_lib/`). *(Atendido.)*
- **CA-05** Suítes verdes (unit + integração + MCP) como gate. *(Atendido —
  60 + 27 + 37.)*
- **CA-06** Documentação obrigatória (`README`, `CHANGELOG`, este PRD)
  atualizada junto da feature.

## 8. Escopo

### Entregue (Caminho 01 — A + I + J)
Pipeline WebDAV idempotente; API HTTP read-only (6 rotas) + Swagger pt-BR; MCP
com 9 tools; validador alfanumérico + `cnpj_lib`; monitor; migração SOPS+age;
CI local.

### Backlog imediato (a confirmar prioridade)
- Rotas `/lookups` e `/busca` na API, simétricas às buscas do MCP.
- Mover índices novos para `database.py::create_indices()`.
- Coluna `periodo` explícita em `controle_importacao`.
- Ativar hooks Discord/Telegram do `monitor/notify.sh`.

### Futuro — caminhos não executados
- **Caminho 02** — "Observatório de deltas + grafo PJ": diff mensal real entre
  safras, grafo de vínculos PJ↔PJ, mapa de calor CNAE × município.
- **Caminho 03** — "Observatório econômico de Rondônia": dashboard regional +
  KYB simplificado (CEIS/CNEP/CEPIM) cruzando com Compras gov.br. *(a confirmar)*

## 9. Restrições e fonte de dados

- **Fonte**: share público Nextcloud da RFB via WebDAV; `RFB_SHARE_TOKEN`
  configurável (se mudar, é config, não reescrita).
- **Base legal**: Decreto 8.777/2016 + LAI permitem redistribuir com atribuição
  à RFB; respeitar o semáforo LGPD documentado.
- **Volumes** (`2026-05`): ~37 ZIPs / ~8 GB comprimidos; banco final ~37–50 GB;
  ~68M empresas, ~71M estabelecimentos, ~27M sócios.
- **Arquitetura preservada**: divisão `main → fetcher → database → notifier`; o
  MCP importa apenas `app.servicos`, nunca `app.rotas`.
