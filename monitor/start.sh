#!/usr/bin/env bash
# start.sh — sobe o collect.py em background com nohup.
#
# - Verifica se já há coletor rodando via .collect.pid + /proc/<pid>.
# - Loga em monitor/collect.log (stderr do collect.py).
# - Imprime PID e dicas de uso ao final.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="${SCRIPT_DIR}/.collect.pid"
LOGFILE="${SCRIPT_DIR}/collect.log"
HTTP_PIDFILE="${SCRIPT_DIR}/.http-server.pid"
HTTP_LOGFILE="${SCRIPT_DIR}/.http-server.log"
HTTP_PORT="${MONITOR_HTTP_PORT:-8765}"
HTTP_BIND="${MONITOR_HTTP_BIND:-127.0.0.1}"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ----- Escolha do Python -------------------------------------------------- #
PYTHON_BIN=""
if [[ -x "${PROJECT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "ERRO: Python 3 não encontrado." >&2
  exit 1
fi

# ----- Já está rodando? --------------------------------------------------- #
if [[ -f "${PIDFILE}" ]]; then
  EXISTING_PID="$(cat "${PIDFILE}" 2>/dev/null || true)"
  if [[ -n "${EXISTING_PID}" ]] && kill -0 "${EXISTING_PID}" 2>/dev/null; then
    echo "Coletor já está rodando (PID=${EXISTING_PID}). Use ./stop.sh para parar."
    exit 0
  fi
  echo "Aviso: lockfile órfão encontrado (.collect.pid=${EXISTING_PID}); removendo."
  rm -f "${PIDFILE}"
fi

# ----- Boot --------------------------------------------------------------- #
echo "Iniciando coletor..."
echo "  Python : ${PYTHON_BIN}"
echo "  Script : ${SCRIPT_DIR}/collect.py"
echo "  Log    : ${LOGFILE}"

cd "${SCRIPT_DIR}"
# Apaga offset pra forçar reconstrução íntegra do status.json a partir do log
# do pipeline. Reparsing é trivial (ms) e evita status.json mutilado se o
# coletor reiniciar no meio de um run.
rm -f "${SCRIPT_DIR}/.collect.offset"
nohup "${PYTHON_BIN}" "${SCRIPT_DIR}/collect.py" "$@" \
  >> "${LOGFILE}" 2>&1 &

NEW_PID=$!
echo "${NEW_PID}" > "${PIDFILE}"

# Dá um instante e confirma que sobreviveu.
sleep 1
if ! kill -0 "${NEW_PID}" 2>/dev/null; then
  echo "ERRO: coletor morreu logo após o boot. Veja ${LOGFILE}." >&2
  rm -f "${PIDFILE}"
  exit 2
fi

# ----- HTTP server p/ dashboard ------------------------------------------ #
# Chromium bloqueia fetch() sobre file:// por CORS, então o dashboard
# precisa ser servido por HTTP. Servidor stdlib, bind em loopback.
HTTP_PID=""
if [[ -f "${HTTP_PIDFILE}" ]]; then
  EXISTING_HTTP_PID="$(cat "${HTTP_PIDFILE}" 2>/dev/null || true)"
  if [[ -n "${EXISTING_HTTP_PID}" ]] && kill -0 "${EXISTING_HTTP_PID}" 2>/dev/null; then
    HTTP_PID="${EXISTING_HTTP_PID}"
    echo "HTTP server já rodando (PID=${HTTP_PID}, porta ${HTTP_PORT})."
  else
    rm -f "${HTTP_PIDFILE}"
  fi
fi

if [[ -z "${HTTP_PID}" ]]; then
  # server.py = http.server + endpoints POST /api/run e /api/stop.
  nohup "${PYTHON_BIN}" "${SCRIPT_DIR}/server.py" \
    --port "${HTTP_PORT}" --bind "${HTTP_BIND}" \
    >> "${HTTP_LOGFILE}" 2>&1 &
  HTTP_PID=$!
  echo "${HTTP_PID}" > "${HTTP_PIDFILE}"
  sleep 1
  if ! kill -0 "${HTTP_PID}" 2>/dev/null; then
    echo "AVISO: HTTP server morreu logo após boot (porta ${HTTP_PORT} em uso?). Veja ${HTTP_LOGFILE}." >&2
    rm -f "${HTTP_PIDFILE}"
    HTTP_PID=""
  else
    echo "HTTP server iniciado (PID=${HTTP_PID}, http://${HTTP_BIND}:${HTTP_PORT}/)."
  fi
fi

cat <<EOF

Coletor iniciado (PID=${NEW_PID}).

  Dashboard HTML     :  http://${HTTP_BIND}:${HTTP_PORT}/dashboard.html
                        xdg-open http://${HTTP_BIND}:${HTTP_PORT}/dashboard.html
  Status no terminal :  ${SCRIPT_DIR}/status.sh
                        watch -n 5 ${SCRIPT_DIR}/status.sh
  Log do coletor     :  tail -f ${LOGFILE}
  Parar              :  ${SCRIPT_DIR}/stop.sh

Status JSON atualizado a cada ~5s em ${SCRIPT_DIR}/status.json
EOF
