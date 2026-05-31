# Estado do projeto — onde paramos

> AMBOS os agentes (Claude Code e Antigravity) DEVEM ler este arquivo no início
> da sessão e ATUALIZAR no fim. É a memória compartilhada — a memória interna de
> cada ferramenta NÃO é vista pela outra.

## Última sessão
- Data / ferramenta: 2026-05-30 / Claude Code
- Branch: main
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
