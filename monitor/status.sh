#!/usr/bin/env bash
# status.sh — viewer rápido em terminal do monitor/status.json.
#
# Imprime um resumo Markdown escaneável com cores ANSI. Útil ad hoc ou via
# `watch -n 5 ./status.sh`.
#
# Dependências: bash + jq.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATUS_FILE="${SCRIPT_DIR}/status.json"

# ----- Verificações iniciais ---------------------------------------------- #
if ! command -v jq >/dev/null 2>&1; then
  echo "ERRO: jq não está instalado." >&2
  echo "  Ubuntu/Debian: sudo apt install jq" >&2
  echo "  Fedora:        sudo dnf install jq" >&2
  exit 2
fi

if [[ ! -f "${STATUS_FILE}" ]]; then
  echo "ERRO: ${STATUS_FILE} não existe. O coletor já foi iniciado?" >&2
  echo "  Dica: rode ./start.sh ou python collect.py --once" >&2
  exit 3
fi

# ----- Cores (desativa se stdout não é TTY) ------------------------------- #
if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_DIM=$'\033[2m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_RED=$'\033[31m'
  C_BLUE=$'\033[34m'
  C_GREY=$'\033[90m'
  C_CYAN=$'\033[36m'
else
  C_RESET=""; C_BOLD=""; C_DIM=""; C_GREEN=""; C_YELLOW=""
  C_RED=""; C_BLUE=""; C_GREY=""; C_CYAN=""
fi

# ----- Helper de leitura via jq ------------------------------------------ #
# Tolera campo ausente/null: devolve string vazia (ou o default fornecido).
jget() {
  local expr="$1" default="${2:-}"
  local val
  val="$(jq -r "${expr} // empty" "${STATUS_FILE}" 2>/dev/null || true)"
  if [[ -z "${val}" || "${val}" == "null" ]]; then
    printf '%s' "${default}"
  else
    printf '%s' "${val}"
  fi
}

STATE="$(jget '.state' 'unknown')"
ALIVE="$(jget '.alive' 'false')"
PID="$(jget '.pid' '?')"
PERIOD="$(jget '.period' '?')"
STARTED_AT="$(jget '.started_at' '?')"
LAST_EVENT_AT="$(jget '.last_event_at' '?')"
ENDED_AT="$(jget '.ended_at' '')"
CURRENT_ACTION="$(jget '.current_action' '(sem ação registrada)')"
TOTAL_ZIPS="$(jget '.total_zips' '0')"
TOTAL_BYTES="$(jget '.total_bytes' '0')"
DL_COUNT="$(jget '.summary.downloaded_count' '0')"
DL_BYTES="$(jget '.summary.downloaded_bytes' '0')"
IN_PROGRESS="$(jget '.summary.downloads_in_progress' '0')"
ING_COUNT="$(jget '.summary.ingested_count' '0')"
ERR_COUNT="$(jget '.summary.errors_count' '0')"
PROGRESS="$(jget '.summary.progress_pct' '0')"
ELAPSED="$(jget '.summary.elapsed_seconds' '0')"
ETA="$(jget '.summary.eta_seconds' '')"

# ----- Helpers de formatação --------------------------------------------- #
human_secs() {
  local s="${1:-0}"
  if [[ -z "${s}" || "${s}" == "null" || "${s}" == "?" ]]; then echo "?"; return; fi
  s=${s%.*}
  [[ -z "${s}" ]] && { echo "?"; return; }
  if (( s < 60 )); then printf "%ds" "${s}"; return; fi
  if (( s < 3600 )); then printf "%dm%02ds" $((s/60)) $((s%60)); return; fi
  printf "%dh%02dm" $((s/3600)) $(((s%3600)/60))
}

human_bytes() {
  local b="${1:-0}"
  [[ -z "${b}" ]] && b=0
  awk -v b="${b}" 'BEGIN{
    if (b >= 1024*1024*1024) printf "%.2f GB", b/(1024*1024*1024);
    else if (b >= 1024*1024) printf "%.1f MB", b/(1024*1024);
    else if (b >= 1024)      printf "%.1f KB", b/1024;
    else                     printf "%d B",  b;
  }'
}

color_for_state() {
  case "$1" in
    running)   echo "${C_BLUE}" ;;
    completed) echo "${C_GREEN}" ;;
    failed)    echo "${C_RED}" ;;
    *)         echo "${C_GREY}" ;;
  esac
}

badge_for_state() {
  local c
  c="$(color_for_state "$1")"
  local upper
  upper="$(echo "$1" | tr '[:lower:]' '[:upper:]')"
  printf "%s%s[ %s ]%s" "${C_BOLD}" "${c}" "${upper}" "${C_RESET}"
}

# Barra de progresso ASCII (largura 40).
draw_bar() {
  local pct="$1" width=40
  local filled
  filled=$(awk -v p="${pct}" -v w="${width}" 'BEGIN{ f=int(p/100*w); if (f<0) f=0; if (f>w) f=w; print f}')
  local empty=$((width - filled))
  local color="${C_GREEN}"
  if awk -v p="${pct}" 'BEGIN{ exit !(p<30) }'; then color="${C_RED}"; fi
  if awk -v p="${pct}" 'BEGIN{ exit !(p>=30 && p<70) }'; then color="${C_YELLOW}"; fi
  printf "%s" "${color}"
  if (( filled > 0 )); then
    printf '█%.0s' $(seq 1 "${filled}")
  fi
  printf "%s" "${C_GREY}"
  if (( empty > 0 )); then
    printf '░%.0s' $(seq 1 "${empty}")
  fi
  LC_NUMERIC=C printf "%s %5.1f%%" "${C_RESET}" "${pct}"
}

alive_label() {
  if [[ "${ALIVE}" == "true" ]]; then
    printf "%s● vivo%s" "${C_GREEN}" "${C_RESET}"
  else
    printf "%s○ morto%s" "${C_GREY}" "${C_RESET}"
  fi
}

# ----- Render ------------------------------------------------------------- #
echo
printf "%s━━━ Pipeline CNPJ ━━━%s  %s\n" "${C_BOLD}${C_CYAN}" "${C_RESET}" "$(badge_for_state "${STATE}")"
printf "  %speríodo%s     %s\n" "${C_DIM}" "${C_RESET}" "${PERIOD}"
printf "  %spid%s         %s  %s\n" "${C_DIM}" "${C_RESET}" "${PID}" "$(alive_label)"
printf "  %siniciado%s    %s\n" "${C_DIM}" "${C_RESET}" "${STARTED_AT}"
printf "  %súltimo evt%s  %s\n" "${C_DIM}" "${C_RESET}" "${LAST_EVENT_AT}"
if [[ -n "${ENDED_AT}" ]]; then
  printf "  %sterminado%s   %s\n" "${C_DIM}" "${C_RESET}" "${ENDED_AT}"
fi
printf "  %selapsed%s     %s" "${C_DIM}" "${C_RESET}" "$(human_secs "${ELAPSED}")"
if [[ -n "${ETA}" ]]; then
  printf "   %sETA%s %s\n" "${C_DIM}" "${C_RESET}" "$(human_secs "${ETA}")"
else
  printf "\n"
fi

echo
printf "  "
draw_bar "${PROGRESS}"
echo
echo

# Contadores em uma linha compacta.
printf "  %sdownloads%s %s/%s (%s de %s)   %sin-progress%s %s   " \
  "${C_DIM}" "${C_RESET}" \
  "${DL_COUNT}" "${TOTAL_ZIPS}" \
  "$(human_bytes "${DL_BYTES}")" "$(human_bytes "${TOTAL_BYTES}")" \
  "${C_DIM}" "${C_RESET}" "${IN_PROGRESS}"
printf "%singestões%s %s   " "${C_DIM}" "${C_RESET}" "${ING_COUNT}"
if (( ERR_COUNT > 0 )); then
  printf "%serros%s %s%d%s\n" "${C_DIM}" "${C_RESET}" "${C_RED}" "${ERR_COUNT}" "${C_RESET}"
else
  printf "%serros%s 0\n" "${C_DIM}" "${C_RESET}"
fi

echo
printf "  %sAção corrente%s\n" "${C_BOLD}" "${C_RESET}"
printf "    %s%s%s\n" "${C_CYAN}" "${CURRENT_ACTION}" "${C_RESET}"

if (( ERR_COUNT > 0 )); then
  echo
  printf "  %sÚltimos erros (até 3)%s\n" "${C_BOLD}${C_RED}" "${C_RESET}"
  jq -r '.errors | (if length > 3 then .[-3:] else . end)[]
         | "    \(.ts) [\(.level)] \(.message)"' "${STATUS_FILE}" \
    | while IFS= read -r line; do
        printf "  %s%s%s\n" "${C_RED}" "${line}" "${C_RESET}"
      done
fi

echo
printf "%sstatus.json:%s %s\n" "${C_DIM}" "${C_RESET}" "${STATUS_FILE}"
echo
