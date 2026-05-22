"""Smoke test: exercita fetcher + database só com os ZIPs pequenos de referência.

Rode da raiz do projeto: `.venv/bin/python tests/smoke_test.py`.
Baixa ~70 KB e popula um banco descartável em segundos — não toca o `dados_cnpj.db` real.
"""
import os
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from notifier import Notifier, load_env
from fetcher import CNPJFetcher
from database import DatabaseManager

SMALL_ZIPS = {"Cnaes.zip", "Motivos.zip", "Municipios.zip",
              "Naturezas.zip", "Paises.zip", "Qualificacoes.zip"}


def main():
    load_env()
    notifier = Notifier()

    dir_temp = Path("temp_smoke").absolute()
    if dir_temp.exists():
        shutil.rmtree(dir_temp)
    dir_temp.mkdir()

    db_path = "smoke_cnpj.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    fetcher = CNPJFetcher(dir_temp=dir_temp, notifier=notifier)
    period = fetcher.latest_period()
    notifier.log_and_notify(f"[smoke] Período mais recente: {period}")

    zips = fetcher.list_zips(period)
    small = [z for z in zips if z["name"] in SMALL_ZIPS]
    notifier.log_and_notify(
        f"[smoke] {len(small)} ZIPs pequenos a baixar (de {len(zips)} total)."
    )

    downloaded = []
    for z in small:
        downloaded.append(fetcher.download_zip(period, z["name"], z["size"]))

    db = DatabaseManager(db_path, notifier)
    db.init_db()
    for f in downloaded:
        ok = db.import_csv_from_zip(str(f))
        notifier.log_and_notify(f"[smoke] {f.name}: ingestão {'OK' if ok else 'FALHOU'}.")
    db.create_indices()

    conn = sqlite3.connect(db_path)
    try:
        for table in ("cnaes", "motivos", "municipios", "naturezas", "paises", "qualificacoes"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            notifier.log_and_notify(f"[smoke] {table}: {count} linhas.")
    finally:
        conn.close()

    notifier.log_and_notify("[smoke] OK — pipeline fetcher→database funcionando.")


if __name__ == "__main__":
    main()
