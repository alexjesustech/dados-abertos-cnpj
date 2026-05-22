"""Orquestra o pipeline de Dados Abertos do CNPJ: fetcher -> database."""
import logging
import os
import shutil
from pathlib import Path

from notifier import Notifier, load_env
from fetcher import CNPJFetcher
from database import DatabaseManager


def main():
    load_env()
    notifier = Notifier()

    dir_temp = Path("temp").absolute()
    if dir_temp.exists():
        notifier.log_and_notify(f'Limpando diretório temporário ("{dir_temp}").')
        shutil.rmtree(dir_temp)
    dir_temp.mkdir(parents=True)

    notifier.log_and_notify("Início da extração e ingestão dos Dados Abertos do CNPJ.")

    period_env = os.getenv("CNPJ_PERIOD", "").strip() or None
    fetcher = CNPJFetcher(dir_temp=dir_temp, notifier=notifier)

    try:
        period, zip_files = fetcher.fetch_all(period_env)
    except Exception as e:
        notifier.log_and_notify(f"Falha no download dos ZIPs: {e}", level=logging.ERROR)
        raise

    notifier.log_and_notify(f"Download concluído ({len(zip_files)} arquivos) para o período {period}.")

    if not zip_files:
        notifier.log_and_notify("Nenhum ZIP baixado — abortando ingestão.", level=logging.WARNING)
        return

    db_path = os.getenv("DB_PATH", "dados_cnpj.db")
    db_manager = DatabaseManager(db_path, notifier)
    db_manager.init_db()

    delete_zip_after = os.getenv("DELETE_ZIP_AFTER", "false").lower() == "true"

    for zip_file in zip_files:
        try:
            success = db_manager.import_csv_from_zip(str(zip_file))
            if success and delete_zip_after:
                notifier.log_and_notify(f"Excluindo {zip_file.name} para liberar espaço.")
                try:
                    os.remove(zip_file)
                except OSError as delete_err:
                    notifier.log_and_notify(
                        f"Erro ao remover {zip_file.name}: {delete_err}",
                        level=logging.WARNING,
                    )
        except Exception as e:
            notifier.log_and_notify(
                f"Falha na ingestão de {zip_file.name}: {e}",
                level=logging.ERROR,
            )

    db_manager.create_indices()
    notifier.log_and_notify("Processamento e ingestão concluídos com sucesso.")


if __name__ == "__main__":
    main()
