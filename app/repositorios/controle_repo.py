"""SELECTs na tabela `controle_importacao` — apoia tool delta_mensal."""
from __future__ import annotations

import sqlite3
from typing import Any


def listar_periodos(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Devolve [{periodo: 'YYYY-MM', arquivos: int, ultima_data: str}, ...]."""
    cur = conn.execute(
        """
        SELECT SUBSTR(data_importacao, 1, 7) AS periodo,
               COUNT(*) AS arquivos,
               MAX(data_importacao) AS ultima_data
          FROM controle_importacao
         GROUP BY SUBSTR(data_importacao, 1, 7)
         ORDER BY periodo DESC
        """
    )
    return [dict(row) for row in cur]


def arquivos_do_periodo(conn: sqlite3.Connection, periodo: str) -> list[dict[str, Any]]:
    """Lista arquivos importados num período YYYY-MM."""
    cur = conn.execute(
        """
        SELECT arquivo, status, data_importacao
          FROM controle_importacao
         WHERE SUBSTR(data_importacao, 1, 7) = ?
         ORDER BY arquivo
        """,
        (periodo,),
    )
    return [dict(row) for row in cur]
