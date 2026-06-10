@AGENTS.md

<!--
NOTA (interop Claude Code ↔ Antigravity):
Este arquivo é apenas um PONTEIRO. A fonte única de verdade é o AGENTS.md na raiz
deste projeto. O Claude Code expande o import `@AGENTS.md` acima e carrega todo o
conteúdo. O Antigravity/Gemini leem AGENTS.md e GEMINI.md (arquivo que
referencia o AGENTS.md em prosa) diretamente.

Por que o ponteiro fica AQUI na raiz (e não em .claude/CLAUDE.md com @../AGENTS.md):
o import com `../` é frágil e, além disso, o Antigravity não procura .claude/CLAUDE.md.
Manter CLAUDE.md na raiz com `@AGENTS.md` (mesmo diretório) é mais simples e robusto.
-->

## Overrides Claude Code (opcional)
<!-- Regras específicas SÓ do Claude Code que não fazem sentido para o Antigravity.
     Deixe vazio se não houver. As rules modulares ficam em .claude/rules/. -->
