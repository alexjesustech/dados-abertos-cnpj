#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coletor de status do pipeline `dados-abertos-cnpj`.

Lê incrementalmente o arquivo de log estruturado do pipeline, parseia eventos
conforme `STATUS_SCHEMA.md` e escreve o snapshot em `monitor/status.json` de
forma atômica (tmp + os.replace), para que o dashboard HTML possa lê-lo
concomitantemente.

Stdlib only (Python 3.12). Sem dependências externas.

Uso:
    python collect.py                 # loop a cada 5s
    python collect.py --interval 2    # loop a cada 2s
    python collect.py --once          # um único tick (útil pra rebuild)
    python collect.py --pid 12345     # PID explícito do main.py

Idempotência:
    Apagar `.collect.offset` faz o coletor reconstruir o estado lendo o log
    inteiro do início.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Constantes e configuração
# --------------------------------------------------------------------------- #

SCHEMA_VERSION = 1

# Fuso horário local: detectado do sistema na inicialização.
# Em base-station é Porto Velho (-04:00), em São Paulo seria (-03:00).
# Calculado em runtime via `datetime.now().astimezone().utcoffset()`.
TZ_LOCAL = datetime.now().astimezone().tzinfo or timezone(timedelta(hours=-3))

# Aceita "YYYY-MM-DD HH:MM:SS,mmm" (com vírgula) ou "." (defesa em profundidade).
RE_LOG_LINE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.]\d{3})\s+"
    r"\[(?P<level>[A-Z]+)\]\s+(?P<msg>.*)$"
)

# Padrões da mensagem (após o prefixo).
RE_PERIODO = re.compile(r"^Período-alvo:\s*(?P<periodo>\d{4}-\d{2})")
RE_TOTAL = re.compile(
    r"^(?P<n>\d+)\s+arquivos\s+ZIP\s+no\s+período\s+(?P<periodo>\d{4}-\d{2})\s+"
    r"\(~(?P<gb>[\d.]+)\s*GB\)\.?"
)
RE_GET = re.compile(
    r"^\[get\]\s+(?P<name>\S+)\s+\((?P<bytes>\d+)\s+bytes,\s+"
    r"tentativa\s+(?P<att>\d+)\)\.?"
)
RE_RESUME = re.compile(
    r"^\[resume\]\s+(?P<name>\S+)\s+de\s+(?P<a>\d+)/(?P<b>\d+)\s+bytes,\s+"
    r"tentativa\s+(?P<att>\d+)\)\.?"
)
RE_SKIP = re.compile(
    r"^\[skip\]\s+(?P<name>\S+)\s+já presente\s+\((?P<bytes>\d+)\s+bytes\)\.?"
)
RE_WARN_TAMANHO = re.compile(r"^\[warn\]\s+(?P<name>\S+):\s+tamanho final")
RE_ERR_TENT = re.compile(r"^\[err\]\s+(?P<name>\S+)\s+tentativa\s+\d+/\d+:")
RE_DOWNLOAD_OK = re.compile(
    r"^Download concluído\s+\((?P<n>\d+)\s+arquivos\)\s+para\s+o período\s+"
    r"(?P<periodo>\d{4}-\d{2})\.?"
)
RE_INICIO_ZIP = re.compile(
    r"^Iniciando leitura por streaming do arquivo ZIP:\s+(?P<zip>\S+?)\.\.\.?"
)
RE_IMPORTANDO = re.compile(
    r"^Importando\s+\S+\s+\(dentro de\s+(?P<zip>\S+)\)\s+para a tabela\s+"
    r"'(?P<tabela>[^']+)'"
)
RE_TABELA_OK = re.compile(
    r"^Tabela\s+'(?P<tabela>[^']+)'\s+finalizada\.\s+Ingeridos\s+"
    r"(?P<rows>[\d,\.]+)\s+registros\s+em\s+(?P<dur>[\d.]+)\s+segundos\.?"
)
RE_FALHA_DOWNLOAD = re.compile(r"^Falha no download dos ZIPs:\s*(?P<msg>.*)")
RE_FALHA_INGEST = re.compile(r"^Falha na ingestão de\s+(?P<zip>\S+):\s*(?P<msg>.*)")

MSG_INICIO = "Início da extração e ingestão dos Dados Abertos do CNPJ."
MSG_SUCESSO_FINAL = "Processamento e ingestão concluídos com sucesso."
MSG_CRIANDO_INDICES = "Criando índices para otimização de consultas..."
MSG_INDICES_OK = "Índices criados com sucesso."

# --------------------------------------------------------------------------- #
# Logging próprio do coletor (stderr; não polui o log do pipeline)
# --------------------------------------------------------------------------- #

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [collect] [%(levelname)s] %(message)s",
)
log = logging.getLogger("collect")


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #


def parse_log_ts(raw: str) -> str:
    """Converte 'YYYY-MM-DD HH:MM:SS,mmm' (fuso local) em ISO 8601 com offset."""
    raw_norm = raw.replace(",", ".")
    dt = datetime.strptime(raw_norm, "%Y-%m-%d %H:%M:%S.%f")
    dt = dt.replace(tzinfo=TZ_LOCAL)
    return dt.isoformat(timespec="seconds")


def now_iso() -> str:
    return datetime.now(TZ_LOCAL).isoformat(timespec="seconds")


def iso_to_epoch(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso).timestamp()
    except ValueError:
        return None


def detect_pid() -> int | None:
    """Tenta achar o PID do `main.py` do pipeline CNPJ.

    Estratégia em camadas:
      1. `pgrep -af python.*main.py` → filtra candidatos.
      2. Para cada PID, lê o `/proc/<pid>/cwd` (symlink) e o
         `/proc/<pid>/cmdline` para confirmar que está rodando dentro do
         diretório do projeto (`dados-abertos-cnpj`).
    Isso evita falso-positivo com outros `main.py` (p.ex. Bazarr no homelab).
    """
    project_marker = "dados-abertos-cnpj"
    try:
        out = subprocess.run(
            ["pgrep", "-af", "python.*main.py"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        log.warning("pgrep não encontrado; informe --pid manualmente")
        return None

    candidates: list[int] = []
    for line in out.stdout.strip().splitlines():
        parts = line.strip().split(None, 1)
        if not parts:
            continue
        try:
            candidates.append(int(parts[0]))
        except ValueError:
            continue

    # 1ª passada: prioriza quem está com cwd dentro do projeto.
    for pid in candidates:
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
        except OSError:
            cwd = ""
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fp:
                cmdline = fp.read().decode("utf-8", errors="replace").replace("\x00", " ")
        except OSError:
            cmdline = ""
        if project_marker in cwd or project_marker in cmdline:
            return pid

    # 2ª passada: fallback — qualquer PID cuja cmdline NÃO contenha caminho
    # de outro projeto (descarta /app/bazarr etc.). Aceita só PIDs cujo
    # executável pareça do venv local.
    for pid in candidates:
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fp:
                cmdline = fp.read().decode("utf-8", errors="replace").replace("\x00", " ")
        except OSError:
            continue
        if ".venv/bin/python" in cmdline and "main.py" in cmdline:
            return pid

    return None


def is_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Existe (não temos permissão pra sinalizar, mas existe).
        return True
    except OSError:
        return False


def format_mb(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024 * 1024:
        return f"{num_bytes / (1024**3):.2f} GB"
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024**2):.0f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes} B"


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Escreve JSON em arquivo .tmp e renomeia atomicamente sobre o destino."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    tmp.write_text(payload + "\n", encoding="utf-8")
    os.replace(tmp, path)


def safe_read_json(path: Path) -> dict[str, Any] | None:
    """Lê JSON tolerando arquivo ausente ou corrompido."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("status.json existente é inválido (%s); recomeçando do zero", exc)
        return None


# --------------------------------------------------------------------------- #
# Estado do coletor
# --------------------------------------------------------------------------- #


class CollectorState:
    """Estado em memória reconstruído a partir do log."""

    def __init__(self, pid: int | None) -> None:
        self.schema_version = SCHEMA_VERSION
        self.pid: int | None = pid
        self.alive: bool = is_alive(pid)
        self.state: str = "running"
        self.started_at: str | None = None
        self.last_event_at: str | None = None
        self.ended_at: str | None = None
        self.period: str | None = None
        self.total_zips: int = 0
        self.total_bytes: int = 0
        self.downloads: list[dict[str, Any]] = []
        self.ingestions: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.current_action: str = "Aguardando primeiro evento do pipeline..."
        # Estado interno (não serializado direto):
        self._criando_indices: bool = False
        self._indices_ok: bool = False
        self._last_msg: str | None = None

    # ------------------------------------------------------------------ #
    # Lookup helpers
    # ------------------------------------------------------------------ #

    def _find_active_download(self, name: str) -> dict[str, Any] | None:
        for d in reversed(self.downloads):
            if d["name"] == name and d["status"] == "in_progress":
                return d
        return None

    def _close_previous_downloads(self, ts: str) -> None:
        """Fecha o download anterior em `in_progress` (heurística do schema)."""
        for d in self.downloads:
            if d["status"] == "in_progress" and d.get("completed_at") is None:
                d["status"] = "done"
                d["completed_at"] = ts

    def _open_ingestion(self, zip_name: str, ts: str) -> dict[str, Any]:
        ingestion = {
            "zip": zip_name,
            "table": None,
            "rows": 0,
            "duration_seconds": 0.0,
            "status": "ok",
            "completed_at": None,
            "_started_at": ts,  # auxiliar; será removido na serialização
        }
        self.ingestions.append(ingestion)
        return ingestion

    def _find_open_ingestion_by_zip(self, zip_name: str) -> dict[str, Any] | None:
        for ing in reversed(self.ingestions):
            if ing["zip"] == zip_name and ing.get("completed_at") is None:
                return ing
        return None

    def _find_open_ingestion_by_table(self, table: str) -> dict[str, Any] | None:
        for ing in reversed(self.ingestions):
            if ing.get("table") == table and ing.get("completed_at") is None:
                return ing
        return None

    # ------------------------------------------------------------------ #
    # Aplicação de uma linha do log
    # ------------------------------------------------------------------ #

    def apply_line(self, raw_line: str) -> None:
        m = RE_LOG_LINE.match(raw_line.rstrip("\n"))
        if not m:
            return
        ts = parse_log_ts(m.group("ts"))
        level = m.group("level")
        msg = m.group("msg").strip()

        self.last_event_at = ts
        self._last_msg = msg

        # --- Marcos do orquestrador ---------------------------------- #
        if msg == MSG_INICIO:
            # Cada "Início da extração..." é um novo run — descarta o estado
            # de qualquer run anterior presente no mesmo log (ex.: smoke test).
            self.started_at = ts
            self.ended_at = None
            self.state = "running"
            self.period = None
            self.total_zips = 0
            self.total_bytes = 0
            self.downloads = []
            self.ingestions = []
            self.errors = []
            self.current_action = "Aguardando primeiro evento do pipeline..."
            self._criando_indices = False
            self._indices_ok = False
            return

        if msg == MSG_SUCESSO_FINAL:
            self.state = "completed"
            self.ended_at = ts
            # Fecha qualquer download/ingestão pendente (defesa).
            self._close_previous_downloads(ts)
            return

        if msg == MSG_CRIANDO_INDICES:
            self._criando_indices = True
            return

        if msg == MSG_INDICES_OK:
            self._indices_ok = True
            return

        m_falha_dl = RE_FALHA_DOWNLOAD.match(msg)
        if m_falha_dl:
            self.errors.append({"ts": ts, "level": level, "message": msg})
            self.state = "failed"
            self.ended_at = ts
            return

        m_falha_ing = RE_FALHA_INGEST.match(msg)
        if m_falha_ing:
            self.errors.append({"ts": ts, "level": level, "message": msg})
            # Tenta marcar a ingestão correspondente como failed.
            ing = self._find_open_ingestion_by_zip(m_falha_ing.group("zip"))
            if ing is not None:
                ing["status"] = "failed"
                ing["completed_at"] = ts
            return

        # --- Fetcher -------------------------------------------------- #
        m_per = RE_PERIODO.match(msg)
        if m_per:
            self.period = m_per.group("periodo")
            return

        m_tot = RE_TOTAL.match(msg)
        if m_tot:
            self.total_zips = int(m_tot.group("n"))
            gb = float(m_tot.group("gb"))
            self.total_bytes = int(round(gb * (1024**3)))
            if not self.period:
                self.period = m_tot.group("periodo")
            return

        m_get = RE_GET.match(msg)
        if m_get:
            # Conclui o download anterior por inferência.
            self._close_previous_downloads(ts)
            name = m_get.group("name")
            self.downloads.append(
                {
                    "name": name,
                    "expected_bytes": int(m_get.group("bytes")),
                    "status": "in_progress",
                    "started_at": ts,
                    "completed_at": None,
                    "attempts": int(m_get.group("att")),
                    "resumed": False,
                }
            )
            return

        m_resume = RE_RESUME.match(msg)
        if m_resume:
            name = m_resume.group("name")
            existing = self._find_active_download(name)
            if existing is None:
                # Cria entrada se ainda não havia [get] correspondente.
                existing = {
                    "name": name,
                    "expected_bytes": int(m_resume.group("b")),
                    "status": "in_progress",
                    "started_at": ts,
                    "completed_at": None,
                    "attempts": int(m_resume.group("att")),
                    "resumed": True,
                }
                self.downloads.append(existing)
            else:
                existing["resumed"] = True
                existing["attempts"] = max(
                    existing.get("attempts", 1), int(m_resume.group("att"))
                )
            return

        m_skip = RE_SKIP.match(msg)
        if m_skip:
            self._close_previous_downloads(ts)
            self.downloads.append(
                {
                    "name": m_skip.group("name"),
                    "expected_bytes": int(m_skip.group("bytes")),
                    "status": "done",
                    "started_at": ts,
                    "completed_at": ts,
                    "attempts": 1,
                    "resumed": False,
                }
            )
            return

        if RE_WARN_TAMANHO.match(msg) or RE_ERR_TENT.match(msg):
            self.errors.append({"ts": ts, "level": level, "message": msg})
            return

        m_dl_ok = RE_DOWNLOAD_OK.match(msg)
        if m_dl_ok:
            self._close_previous_downloads(ts)
            return

        # --- Database ------------------------------------------------- #
        m_ini_zip = RE_INICIO_ZIP.match(msg)
        if m_ini_zip:
            # Linha sinaliza que terminou o download (se ainda estiver aberto).
            self._close_previous_downloads(ts)
            self._open_ingestion(m_ini_zip.group("zip"), ts)
            return

        m_imp = RE_IMPORTANDO.match(msg)
        if m_imp:
            ing = self._find_open_ingestion_by_zip(m_imp.group("zip"))
            if ing is None:
                ing = self._open_ingestion(m_imp.group("zip"), ts)
            ing["table"] = m_imp.group("tabela")
            return

        m_tab_ok = RE_TABELA_OK.match(msg)
        if m_tab_ok:
            tabela = m_tab_ok.group("tabela")
            ing = self._find_open_ingestion_by_table(tabela)
            if ing is None:
                # Fallback: pega a última ingestão aberta.
                for cand in reversed(self.ingestions):
                    if cand.get("completed_at") is None:
                        ing = cand
                        break
            if ing is not None:
                ing["table"] = tabela
                ing["rows"] = int(m_tab_ok.group("rows").replace(",", "").replace(".", ""))
                ing["duration_seconds"] = float(m_tab_ok.group("dur"))
                ing["completed_at"] = ts
                ing["status"] = "ok"
            return

        # Demais linhas (level WARNING/ERROR genéricas) viram erro.
        if level in ("WARNING", "ERROR", "CRITICAL"):
            self.errors.append({"ts": ts, "level": level, "message": msg})
            return

        # Ignora silenciosamente o que não bate em nenhum padrão.

    # ------------------------------------------------------------------ #
    # Derivações por tick
    # ------------------------------------------------------------------ #

    def _downloaded_bytes(self) -> int:
        return sum(d["expected_bytes"] for d in self.downloads if d["status"] == "done")

    def _downloads_in_progress(self) -> list[dict[str, Any]]:
        return [d for d in self.downloads if d["status"] == "in_progress"]

    def _open_ingestions(self) -> list[dict[str, Any]]:
        return [i for i in self.ingestions if i.get("completed_at") is None]

    def _ingested_count(self) -> int:
        return sum(1 for i in self.ingestions if i.get("status") == "ok" and i.get("completed_at"))

    def compute_current_action(self) -> str:
        # 1. Download em progresso
        in_prog = self._downloads_in_progress()
        if in_prog:
            d = in_prog[-1]
            size = format_mb(d["expected_bytes"])
            return f"Baixando {d['name']} ({size}, tentativa {d['attempts']})"

        # 2. Ingestão aberta
        opens = self._open_ingestions()
        if opens:
            ing = opens[-1]
            table = ing.get("table") or "?"
            return f"Ingerindo {ing['zip']} → tabela {table}"

        # 3. Criando índices
        if self._criando_indices and not self._indices_ok:
            return "Criando índices"

        # 4. Estado terminal
        if self.state == "completed":
            return "Concluído"
        if self.state == "failed":
            return "Falha"

        # 5. Fallback: última mensagem do log
        if self._last_msg:
            return f"… {self._last_msg}"
        return "Aguardando primeiro evento do pipeline..."

    def compute_progress_pct(self) -> float:
        download_ratio = 0.0
        if self.total_bytes > 0:
            download_ratio = min(1.0, self._downloaded_bytes() / self.total_bytes)
        ingest_ratio = 0.0
        if self.total_zips > 0:
            ingest_ratio = min(1.0, self._ingested_count() / self.total_zips)
        return round(60.0 * download_ratio + 40.0 * ingest_ratio, 2)

    def compute_eta_seconds(self, elapsed_seconds: float) -> int | None:
        pct = self.compute_progress_pct()
        if pct <= 1.0 or elapsed_seconds < 30:
            return None
        # ETA linear simples a partir do percentual e do elapsed.
        total = elapsed_seconds * (100.0 / pct)
        eta = total - elapsed_seconds
        if eta < 0:
            return 0
        return int(eta)

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def to_status_dict(self) -> dict[str, Any]:
        # Atualiza alive antes de serializar.
        self.alive = is_alive(self.pid)

        elapsed = 0
        start_epoch = iso_to_epoch(self.started_at)
        end_epoch = iso_to_epoch(self.ended_at) or time.time()
        if start_epoch:
            elapsed = max(0, int(end_epoch - start_epoch))

        downloaded_bytes = self._downloaded_bytes()
        downloaded_count = sum(1 for d in self.downloads if d["status"] == "done")
        ingested_count = self._ingested_count()

        current_action = self.compute_current_action()
        self.current_action = current_action

        # Sanitiza ingestions (remove campo auxiliar privado).
        ingestions_out = []
        for ing in self.ingestions:
            ingestions_out.append(
                {
                    "zip": ing["zip"],
                    "table": ing.get("table"),
                    "rows": ing.get("rows", 0),
                    "duration_seconds": ing.get("duration_seconds", 0.0),
                    "status": ing.get("status", "ok"),
                    "completed_at": ing.get("completed_at"),
                }
            )

        return {
            "schema_version": self.schema_version,
            "pid": self.pid,
            "alive": self.alive,
            "state": self.state,
            "started_at": self.started_at,
            "last_event_at": self.last_event_at,
            "ended_at": self.ended_at,
            "period": self.period,
            "total_zips": self.total_zips,
            "total_bytes": self.total_bytes,
            "downloads": self.downloads,
            "ingestions": ingestions_out,
            "errors": self.errors,
            "current_action": current_action,
            "summary": {
                "downloaded_count": downloaded_count,
                "downloaded_bytes": downloaded_bytes,
                "ingested_count": ingested_count,
                "downloads_in_progress": len(self._downloads_in_progress()),
                "errors_count": len(self.errors),
                "progress_pct": self.compute_progress_pct(),
                "elapsed_seconds": elapsed,
                "eta_seconds": self.compute_eta_seconds(elapsed),
            },
        }


# --------------------------------------------------------------------------- #
# Leitura incremental do log
# --------------------------------------------------------------------------- #


class LogTailer:
    """Lê o log incrementalmente, lembrando do offset entre execuções."""

    def __init__(self, log_path: Path, offset_path: Path) -> None:
        self.log_path = log_path
        self.offset_path = offset_path
        self.offset = self._load_offset()

    def _load_offset(self) -> int:
        if not self.offset_path.exists():
            return 0
        try:
            return max(0, int(self.offset_path.read_text(encoding="utf-8").strip()))
        except (ValueError, OSError):
            return 0

    def _save_offset(self) -> None:
        try:
            tmp = self.offset_path.with_suffix(self.offset_path.suffix + ".tmp")
            tmp.write_text(str(self.offset), encoding="utf-8")
            os.replace(tmp, self.offset_path)
        except OSError as exc:
            log.warning("não foi possível persistir offset: %s", exc)

    def read_new_lines(self) -> list[str]:
        if not self.log_path.exists():
            return []
        try:
            size = self.log_path.stat().st_size
            # Detecta truncamento/rotate: se o arquivo encolheu, reinicia.
            if size < self.offset:
                log.info("log encolheu (%d < %d); reiniciando offset", size, self.offset)
                self.offset = 0
            with self.log_path.open("r", encoding="utf-8", errors="replace") as fp:
                fp.seek(self.offset)
                data = fp.read()
                self.offset = fp.tell()
        except OSError as exc:
            log.warning("falha lendo log: %s", exc)
            return []
        self._save_offset()
        if not data:
            return []
        # Mantém só linhas completas (com newline final); deixa parcial pro próximo tick.
        lines = data.splitlines(keepends=True)
        complete = [ln for ln in lines if ln.endswith("\n")]
        if len(complete) < len(lines):
            # Devolve o offset pra antes da linha incompleta.
            incomplete_size = sum(len(ln.encode("utf-8")) for ln in lines if not ln.endswith("\n"))
            self.offset -= incomplete_size
            self._save_offset()
        return complete


# --------------------------------------------------------------------------- #
# Notificação de término
# --------------------------------------------------------------------------- #


def disparar_notificacao(monitor_dir: Path, state: str, resumo: str) -> None:
    """Chama ./notify.sh state resumo, sem travar se falhar."""
    script = monitor_dir / "notify.sh"
    if not script.exists():
        log.warning("notify.sh não encontrado em %s", script)
        return
    try:
        subprocess.run(
            ["bash", str(script), state, resumo],
            cwd=str(monitor_dir),
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("falha disparando notify.sh: %s", exc)


def resumo_para_notificacao(snap: dict[str, Any]) -> str:
    s = snap.get("summary", {})
    period = snap.get("period") or "?"
    if snap["state"] == "completed":
        return (
            f"Período {period} concluído — "
            f"{s.get('downloaded_count', 0)}/{snap.get('total_zips', 0)} ZIPs, "
            f"{s.get('ingested_count', 0)} ingestões, "
            f"{s.get('errors_count', 0)} erros."
        )
    return (
        f"Pipeline FALHOU (período {period}) — "
        f"{s.get('downloaded_count', 0)}/{snap.get('total_zips', 0)} ZIPs baixados, "
        f"{s.get('errors_count', 0)} erros registrados."
    )


# --------------------------------------------------------------------------- #
# Loop principal
# --------------------------------------------------------------------------- #


def tick(
    state: CollectorState,
    tailer: LogTailer,
    run_out_path: Path,
    status_path: Path,
    notify_sent_path: Path,
    monitor_dir: Path,
) -> dict[str, Any]:
    """Executa um ciclo: lê log → aplica → checa término → escreve status."""

    for line in tailer.read_new_lines():
        try:
            state.apply_line(line)
        except (ValueError, KeyError) as exc:  # robustez extrema
            log.debug("linha ignorada (%s): %s", exc, line.rstrip())

    # Detecção de término por morte de processo (sem linha de sucesso).
    if state.state == "running" and state.pid and not is_alive(state.pid):
        if not any(MSG_SUCESSO_FINAL in (e.get("message") or "") for e in state.errors):
            log.info("processo %s morreu sem linha de sucesso; marcando failed", state.pid)
            state.state = "failed"
            state.ended_at = now_iso()
            # Anexa tail dos últimos 20 eventos do log + run.out como contexto.
            tail = _tail_lines(tailer.log_path, 20)
            if tail:
                state.errors.append(
                    {
                        "ts": state.ended_at,
                        "level": "ERROR",
                        "message": "[coletor] processo morreu sem sucesso. Tail log:\n"
                        + "".join(tail),
                    }
                )
            ro = _tail_lines(run_out_path, 20)
            if ro:
                state.errors.append(
                    {
                        "ts": state.ended_at,
                        "level": "ERROR",
                        "message": "[coletor] Tail run.out:\n" + "".join(ro),
                    }
                )

    snap = state.to_status_dict()
    atomic_write_json(status_path, snap)

    # Disparo único de notificação.
    if snap["state"] in ("completed", "failed") and not notify_sent_path.exists():
        resumo = resumo_para_notificacao(snap)
        log.info("disparando notificação (%s): %s", snap["state"], resumo)
        disparar_notificacao(monitor_dir, snap["state"], resumo)
        try:
            notify_sent_path.write_text(
                f"{snap['state']} @ {now_iso()}\n{resumo}\n", encoding="utf-8"
            )
        except OSError as exc:
            log.warning("não foi possível gravar notify.sent: %s", exc)

    return snap


def _tail_lines(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fp:
            lines = fp.readlines()
        return lines[-n:]
    except OSError:
        return []


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    project = here.parent

    parser = argparse.ArgumentParser(description="Coletor de status do pipeline CNPJ.")
    parser.add_argument(
        "--pid",
        type=int,
        default=None,
        help="PID do main.py (auto-detecta via pgrep se omitido).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Intervalo entre ticks em segundos (default: 5).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa um único tick e sai (útil pra rebuild manual).",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=project / "dados-abertos-cnpj.log",
        help="Caminho do log do pipeline.",
    )
    parser.add_argument(
        "--run-out",
        type=Path,
        default=project / "run.out",
        help="Caminho do stdout/stderr do processo.",
    )
    parser.add_argument(
        "--status",
        type=Path,
        default=here / "status.json",
        help="Caminho de saída do status.json.",
    )
    parser.add_argument(
        "--linger-seconds",
        type=int,
        default=60,
        help="Quantos segundos manter rodando após estado terminal (default: 60).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    monitor_dir: Path = args.status.parent
    offset_path = monitor_dir / ".collect.offset"
    notify_sent_path = monitor_dir / "notify.sent"

    pid = args.pid or detect_pid()
    if pid:
        log.info("monitorando PID=%s", pid)
    else:
        log.warning("nenhum PID detectado; rodando em modo passivo (só leitura do log)")

    state = CollectorState(pid)
    tailer = LogTailer(args.log, offset_path)

    # Trata sinais para encerrar limpo.
    stop_flag = {"stop": False}

    def _handle(_sig, _frame):
        stop_flag["stop"] = True

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)

    if args.once:
        snap = tick(state, tailer, args.run_out, args.status, notify_sent_path, monitor_dir)
        log.info(
            "tick único: state=%s progress=%.1f%% downloads=%d ingestões=%d",
            snap["state"],
            snap["summary"]["progress_pct"],
            snap["summary"]["downloaded_count"],
            snap["summary"]["ingested_count"],
        )
        return 0

    terminal_deadline: float | None = None
    while not stop_flag["stop"]:
        try:
            snap = tick(
                state, tailer, args.run_out, args.status, notify_sent_path, monitor_dir
            )
        except Exception as exc:  # pylint: disable=broad-except
            log.error("erro no tick (continuando): %s", exc, exc_info=True)
            snap = None

        if snap and snap["state"] in ("completed", "failed") and terminal_deadline is None:
            terminal_deadline = time.time() + args.linger_seconds
            log.info(
                "estado terminal (%s); coletor permanecerá ativo por %ds",
                snap["state"],
                args.linger_seconds,
            )

        if terminal_deadline is not None and time.time() >= terminal_deadline:
            log.info("janela de linger encerrada; saindo.")
            break

        # Sleep "fragmentado" pra responder rápido a sinais.
        remaining = args.interval
        step = 0.5
        while remaining > 0 and not stop_flag["stop"]:
            time.sleep(min(step, remaining))
            remaining -= step

    log.info("coletor encerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
