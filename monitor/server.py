"""Servidor HTTP local do monitor.

Substitui `python -m http.server` adicionando endpoints POST que permitem
disparar e parar o pipeline (main.py) direto da UI do dashboard. Bind
exclusivo em loopback (sem auth, então não exponha na LAN sem cuidado).

Endpoints:
  GET  /<arquivo>     -> serve estáticos da pasta monitor/ (igual http.server)
  POST /api/run       -> dispara main.py em background; recusa se já vivo
  POST /api/stop      -> manda SIGTERM no pipeline ativo

Sem dependências externas (stdlib only). Lê o PID corrente do pipeline a
partir do `status.json` mantido pelo coletor — fonte única de verdade.
"""

import argparse
import http.server
import json
import os
import signal
import socketserver
import subprocess
import sys
from pathlib import Path


class MonitorHandler(http.server.SimpleHTTPRequestHandler):
    # Atributos de classe injetados em make_handler()
    project_dir: Path = None  # type: ignore
    monitor_dir: Path = None  # type: ignore

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s - %s\n" % (
            self.log_date_time_string(), self.address_string(), fmt % args
        ))

    # ---------- POST ----------
    def do_POST(self):
        path = self.path.split('?', 1)[0].rstrip('/')
        if path == '/api/run':
            return self._handle_run()
        if path == '/api/stop':
            return self._handle_stop()
        self._json(404, {"ok": False, "error": "endpoint desconhecido"})

    def _handle_run(self):
        pid = self._current_pipeline_pid()
        if pid:
            return self._json(409, {
                "ok": False,
                "error": "pipeline já em execução",
                "pid": pid,
            })

        python = self._project_python()
        if not python:
            return self._json(500, {
                "ok": False,
                "error": ".venv/bin/python não encontrado no projeto",
            })

        run_out = self.project_dir / "run.out"
        main_py = self.project_dir / "main.py"
        if not main_py.is_file():
            return self._json(500, {
                "ok": False,
                "error": f"main.py não encontrado em {self.project_dir}",
            })

        try:
            fp = open(run_out, "ab")
            proc = subprocess.Popen(
                [str(python), "-u", str(main_py)],
                cwd=str(self.project_dir),
                stdout=fp,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,  # nohup-like: desvincula do servidor
            )
            # fp fica aberto no processo filho; fechá-lo aqui não derruba o stream
            fp.close()
        except Exception as e:
            return self._json(500, {"ok": False, "error": f"falha ao iniciar: {e}"})

        return self._json(200, {
            "ok": True,
            "pid": proc.pid,
            "message": f"pipeline iniciado (PID={proc.pid})",
        })

    def _handle_stop(self):
        pid = self._current_pipeline_pid()
        if not pid:
            return self._json(404, {
                "ok": False,
                "error": "nenhum pipeline ativo",
            })
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return self._json(404, {"ok": False, "error": "processo não existe mais"})
        except PermissionError:
            return self._json(403, {"ok": False, "error": "sem permissão (UID diferente)"})
        return self._json(200, {
            "ok": True,
            "pid": pid,
            "message": f"SIGTERM enviado para PID={pid}",
        })

    # ---------- helpers ----------
    def _current_pipeline_pid(self):
        """Lê status.json; retorna pid se vivo (kill -0 ok), senão None."""
        status_path = self.monitor_dir / "status.json"
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        pid = data.get("pid")
        alive_flag = data.get("alive")
        if not pid or not alive_flag:
            return None
        try:
            os.kill(int(pid), 0)
            return int(pid)
        except (ProcessLookupError, ValueError):
            return None
        except PermissionError:
            # Existe mas em outro UID — considera "vivo" pra evitar duplicar
            return int(pid)

    def _project_python(self):
        venv = self.project_dir / ".venv" / "bin" / "python"
        return venv if venv.is_file() else None

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def make_handler(monitor_dir: Path, project_dir: Path):
    class Handler(MonitorHandler):
        pass
    Handler.monitor_dir = monitor_dir
    Handler.project_dir = project_dir
    # SimpleHTTPRequestHandler usa o cwd; injetamos `directory=` no init.
    def init(self, *args, **kw):
        super(Handler, self).__init__(*args, directory=str(monitor_dir), **kw)
    Handler.__init__ = init
    return Handler


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("MONITOR_HTTP_PORT", "8765")))
    parser.add_argument("--bind",
                        default=os.environ.get("MONITOR_HTTP_BIND", "127.0.0.1"))
    parser.add_argument("--monitor-dir",
                        default=str(Path(__file__).resolve().parent))
    parser.add_argument("--project-dir",
                        default=str(Path(__file__).resolve().parent.parent))
    args = parser.parse_args()

    monitor_dir = Path(args.monitor_dir).resolve()
    project_dir = Path(args.project_dir).resolve()

    Handler = make_handler(monitor_dir, project_dir)
    server = ThreadingServer((args.bind, args.port), Handler)
    sys.stderr.write(
        f"[server] http://{args.bind}:{args.port}/ "
        f"(monitor={monitor_dir}, project={project_dir})\n"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
