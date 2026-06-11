# Estado do projeto — onde paramos

> **Regra de rotação (vigente desde 2026-06-11 — canônica no meta-repo `~/projects`,
> replicada aqui):** manter este arquivo **enxuto (< ~200 linhas)**. Na atualização de
> fim de sessão, se passar de ~200 linhas, a poda acontece na **MESMA sessão** (item da
> DoD documental). O excedente roda **verbatim** (nunca resumido/reescrito — auditável)
> para `docs/ESTADO-arquivo.md` (criado na 1ª rotação), em blocos `## Rotação AAAA-MM-DD`
> (mais recente no topo). Por seção: **Snapshot** = só estado vigente; **Pendências** =
> `- [x]` fechadas saem na rotação seguinte ao fechamento, `- [ ]` abertas NUNCA rodam;
> **Decisões** = manter as últimas ~10; **Histórico** = manter as últimas ~8–10 entradas
> (append-only: mover ≠ reescrever); **Armadilhas** = rodam por obsolescência, nunca por
> idade. O arquivo morto NÃO é leitura obrigatória de início de sessão.

> AMBOS os agentes (Claude Code e Antigravity) DEVEM ler este arquivo no início
> da sessão e ATUALIZAR no fim. É a memória compartilhada — a memória interna de
> cada ferramenta NÃO é vista pela outra.

## Última sessão
- Data / ferramenta: 2026-06-11 / Claude Code (manutenção de governança da workstation)
- **`.env.sops.yaml` desversionado** (`git rm --cached` + `.gitignore`) — política nova da
  workstation (ciphertext fora do git); backup = secure note `env — dados-abertos-cnpj`
  no Bitwarden Personal Vault (fingerprint conferido). `AGENTS.md` § Segredos e
  `CHANGELOG` atualizados. Sem mudança de código; uso via `bin/with-env` inalterado.
  Rotação dos valores expostos no histórico = pendência da workstation
  (`~/projects/docs/ESTADO.md`).
- 2026-06-11 — replicada a diretiva global "verificar o remoto no início de sessão" (linha-ponteiro no AGENTS.md).

## Sessão anterior
- Data / ferramenta: 2026-06-10 / Claude Code
- Branch: main
- Onde paramos: **commitada a migração interop multi-LLM** que estava solta no working
  tree (higiene pré-reestruturação da workstation): `AGENTS.md` fonte única (+ correção
  da referência caduca ao symlink `GEMINI.md → CLAUDE.md`), `CLAUDE.md` ponteiro,
  `GEMINI.md` híbrido, `.claude/` versionado, `.opencode/` + `opencode.json`. Sem
  mudança de código. **Ciente:** o repo será movido para `develop/dados-abertos-cnpj`
  na Fase 4 da reestruturação (`~/projects/docs/plans/2026-06-07-selfhost-mesmo-host.md`).

## Sessão anterior (2026-05-30 — branch-guard)
- Onde paramos: propagado o branch-guard (camada 3 do fluxo `/branch` da workstation)
  ao hook `.githooks/pre-commit` — bloqueia commit direto em `main`/`master`, compondo
  com o `gitleaks` já existente. Este repo commita governança/infra direto na `main`
  (`hooks.allowMainCommit true` configurado).
- Decisões tomadas nesta sessão: o pre-commit agora tem duas defesas em profundidade
  (branch-guard + gitleaks); escape per-repo `git config hooks.allowMainCommit true`
  ou pontual `ALLOW_MAIN_COMMIT=1`. Nunca usar `--no-verify`.

## Sessão anterior
- Data / ferramenta: 2026-05-30 / Antigravity
- Onde paramos: montagem da estrutura de interoperabilidade Claude ↔ Antigravity
  (AGENTS.md fonte única, CLAUDE.md ponteiro, GEMINI.md híbrido @AGENTS.md+prosa, rules modulares).
- Decisões tomadas nesta sessão: AGENTS.md vira fonte única; CLAUDE.md = @AGENTS.md; GEMINI.md = @AGENTS.md + fallback em prosa.

## Pendências abertas
- [ ] Verificar empiricamente se esta versão do Antigravity lê `<proj>/AGENTS.md`
      (se não ler, o `GEMINI.md` instrui o agente a abrir e seguir o `AGENTS.md`).

## Decisões arquiteturais recentes (resumo; canônico nos ADRs)
- Implementação de API HTTP local (FastAPI) e MCP server (FastMCP) para consumo read-only do banco SQLite de CNPJs.

## Armadilhas / contexto que não está óbvio no código
- `synchronous=OFF` no SQLite torna o banco vulnerável a crash de OS (aceitável pois o pipeline é re-executável).
- O run cria/reseta `temp/` no início — arquivos parciais do run anterior não são preservados.
- É estritamente proibido editar o arquivo `.env.sops.yaml` diretamente; sempre use o wrapper ou `sops .env.sops.yaml` para não corromper o MAC.
