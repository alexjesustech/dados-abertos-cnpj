"""Factory de conexão SQLite read-only para a API.

A API nunca escreve. Abrir com URI ``?mode=ro`` é a única defesa real
contra um INSERT/UPDATE acidental. WAL (configurado pelo pipeline) permite
N readers concorrentes mesmo durante import.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def _uri_para(path: Path) -> str:
    """Monta URI sqlite read-only a partir de Path absoluto."""
    return f"file:{path.resolve()}?mode=ro"


@contextmanager
def conectar(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Abre conexão read-only com row_factory e fecha no fim do context."""
    conn = sqlite3.connect(_uri_para(db_path), uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
