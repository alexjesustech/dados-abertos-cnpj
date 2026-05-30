"""SELECTs na tabela `socios` (sem PK no schema atual)."""

from __future__ import annotations

import sqlite3
from typing import Any

_COLUNAS = """
    cnpj_basico, identificador_socio, nome_socio_razao_social, cnpj_cpf_socio,
    qualificacao_socio, data_entrada_sociedade, pais,
    representante_legal, nome_do_representante, qualificacao_representante_legal,
    faixa_etaria
"""


def contar_socios(conn: sqlite3.Connection, cnpj_basico: str) -> int:
    cur = conn.execute(
        "SELECT COUNT(*) AS c FROM socios WHERE cnpj_basico = ?",
        (cnpj_basico,),
    )
    return int(cur.fetchone()["c"])


def listar_por_basico(
    conn: sqlite3.Connection,
    cnpj_basico: str,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    cur = conn.execute(
        f"""
        SELECT {_COLUNAS}
          FROM socios
         WHERE cnpj_basico = ?
         ORDER BY identificador_socio, nome_socio_razao_social
         LIMIT ? OFFSET ?
        """,
        (cnpj_basico, limit, offset),
    )
    return [dict(row) for row in cur]


def contar_por_documento(conn: sqlite3.Connection, documento: str) -> int:
    cur = conn.execute(
        "SELECT COUNT(*) AS c FROM socios WHERE cnpj_cpf_socio = ?",
        (documento,),
    )
    return int(cur.fetchone()["c"])


def listar_por_documento(
    conn: sqlite3.Connection,
    documento: str,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    """Vínculos: empresas onde `documento` aparece como sócio.

    `documento` é CPF mascarado (``***NNNNNN**``) ou CNPJ de 14 chars.
    Performance ruim sem `idx_socios_documento` — ver migrations/.
    """
    cur = conn.execute(
        f"""
        SELECT {_COLUNAS}
          FROM socios
         WHERE cnpj_cpf_socio = ?
         ORDER BY cnpj_basico
         LIMIT ? OFFSET ?
        """,
        (documento, limit, offset),
    )
    return [dict(row) for row in cur]
