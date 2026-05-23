#!/usr/bin/env bash
# notify.sh — dispara notificação de desktop quando o pipeline termina.
#
# Uso: ./notify.sh <state> <resumo>
#   state  : "completed" | "failed"
#   resumo : string curta com o resultado
#
# Sempre faz append em monitor/notifications.log. Se `notify-send` não estiver
# disponível, apenas registra um aviso (não falha).

set -u  # -e propositalmente omitido: notify-send pode falhar e não queremos
        # abortar o append no log.

STATE="${1:-unknown}"
RESUMO="${2:-(sem resumo)}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/notifications.log"
TS="$(date -Iseconds)"

case "${STATE}" in
  completed)
    URGENCY="normal"
    ICONE="dialog-information"
    TITULO="Pipeline CNPJ concluído"
    ;;
  failed)
    URGENCY="critical"
    ICONE="dialog-error"
    TITULO="Pipeline CNPJ FALHOU"
    ;;
  *)
    URGENCY="normal"
    ICONE="dialog-information"
    TITULO="Pipeline CNPJ (${STATE})"
    ;;
esac

# Append no log de notificações.
echo "[${TS}] ${STATE}: ${RESUMO}" >> "${LOG_FILE}"

if command -v notify-send >/dev/null 2>&1; then
  # -t 0 = nunca expira (usuário fecha manualmente).
  notify-send \
    -u "${URGENCY}" \
    -i "${ICONE}" \
    -a "dados-abertos-cnpj" \
    -t 0 \
    "${TITULO}" \
    "${RESUMO}" \
    || echo "[${TS}] aviso: notify-send retornou erro" >> "${LOG_FILE}"
else
  echo "[${TS}] aviso: notify-send não está no PATH (instale libnotify-bin)" >> "${LOG_FILE}"
fi

# ---------------------------------------------------------------------------
# Hook futuro — webhook Discord / Telegram.
# Descomente e ajuste quando quiser ativar notificação remota.
#
# if [[ -n "${DISCORD_WEBHOOK_URL:-}" ]]; then
#   curl -sS -X POST -H "Content-Type: application/json" \
#     -d "{\"content\": \"**${TITULO}** — ${RESUMO}\"}" \
#     "${DISCORD_WEBHOOK_URL}" >/dev/null || true
# fi
#
# if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${TELEGRAM_CHAT_ID:-}" ]]; then
#   curl -sS -X POST \
#     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
#     -d "chat_id=${TELEGRAM_CHAT_ID}" \
#     -d "text=${TITULO} — ${RESUMO}" >/dev/null || true
# fi
# ---------------------------------------------------------------------------

exit 0
