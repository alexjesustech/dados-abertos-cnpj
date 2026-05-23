#!/usr/bin/env bash
# stop.sh — encerra o collect.py (SIGTERM, com fallback SIGKILL).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="${SCRIPT_DIR}/.collect.pid"
HTTP_PIDFILE="${SCRIPT_DIR}/.http-server.pid"

# Encerra o HTTP server primeiro (se houver).
if [[ -f "${HTTP_PIDFILE}" ]]; then
  HTTP_PID="$(cat "${HTTP_PIDFILE}" 2>/dev/null || true)"
  if [[ -n "${HTTP_PID}" ]] && kill -0 "${HTTP_PID}" 2>/dev/null; then
    echo "Encerrando HTTP server (PID=${HTTP_PID})..."
    kill -TERM "${HTTP_PID}" 2>/dev/null || true
    sleep 0.5
    if kill -0 "${HTTP_PID}" 2>/dev/null; then
      kill -KILL "${HTTP_PID}" 2>/dev/null || true
    fi
  fi
  rm -f "${HTTP_PIDFILE}"
fi

if [[ ! -f "${PIDFILE}" ]]; then
  echo "Coletor não está rodando (sem .collect.pid)."
  exit 0
fi

PID="$(cat "${PIDFILE}" 2>/dev/null || true)"
if [[ -z "${PID}" ]] || ! kill -0 "${PID}" 2>/dev/null; then
  echo "PID ${PID:-?} não está mais vivo; removendo lockfile."
  rm -f "${PIDFILE}"
  exit 0
fi

echo "Enviando SIGTERM para PID=${PID}..."
kill -TERM "${PID}" 2>/dev/null || true

# Aguarda até 10s pelo encerramento gracioso.
for _ in $(seq 1 20); do
  if ! kill -0 "${PID}" 2>/dev/null; then
    rm -f "${PIDFILE}"
    echo "Coletor encerrado."
    exit 0
  fi
  sleep 0.5
done

echo "Coletor não respondeu a SIGTERM em 10s; enviando SIGKILL..."
kill -KILL "${PID}" 2>/dev/null || true
sleep 0.5
if kill -0 "${PID}" 2>/dev/null; then
  echo "ERRO: PID ${PID} ainda vivo após SIGKILL." >&2
  exit 1
fi
rm -f "${PIDFILE}"
echo "Coletor encerrado (forçado)."
