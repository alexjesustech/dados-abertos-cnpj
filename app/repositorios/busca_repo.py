"""Queries agregadas pra tools MCP de busca/exploração."""

from __future__ import annotations

import sqlite3
from typing import Any


def cnaes_por_municipio(
    conn: sqlite3.Connection,
    municipio_codigo: str,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    """Top-N CNAEs por contagem de estabelecimentos no município.

    Usa `idx_estab_mun` + GROUP BY cnae_fiscal_principal. Sem ORDER BY no
    índice, então com município grande (São Paulo) pode ser pesado — limite
    a 100-200 por consulta.
    """
    cur = conn.execute(
        """
        SELECT cnae_fiscal_principal AS cnae,
               COUNT(*) AS total
          FROM estabelecimentos
         WHERE municipio = ?
         GROUP BY cnae_fiscal_principal
         ORDER BY total DESC
         LIMIT ? OFFSET ?
        """,
        (municipio_codigo, limit, offset),
    )
    return [dict(row) for row in cur]


def contar_cnaes_por_municipio(conn: sqlite3.Connection, municipio_codigo: str) -> int:
    cur = conn.execute(
        """
        SELECT COUNT(DISTINCT cnae_fiscal_principal) AS c
          FROM estabelecimentos
         WHERE municipio = ?
        """,
        (municipio_codigo,),
    )
    return int(cur.fetchone()["c"])


def empresas_por_cnae(
    conn: sqlite3.Connection,
    cnae: str,
    municipio_codigo: str | None,
    uf: str | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    """Lista (basico, razao_social, situacao, municipio, uf) por CNAE principal.

    Filtros opcionais por município/UF. Join com `empresas` pra puxar razão social.
    """
    where = ["e.cnae_fiscal_principal = ?"]
    params: list[Any] = [cnae]
    if municipio_codigo:
        where.append("e.municipio = ?")
        params.append(municipio_codigo)
    if uf:
        where.append("e.uf = ?")
        params.append(uf.upper())
    where_sql = " AND ".join(where)
    params.extend([limit, offset])
    cur = conn.execute(
        f"""
        SELECT e.cnpj_basico, e.cnpj_ordem, e.cnpj_dv,
               emp.razao_social,
               e.situacao_cadastral,
               e.municipio, e.uf
          FROM estabelecimentos AS e
          LEFT JOIN empresas AS emp ON emp.cnpj_basico = e.cnpj_basico
         WHERE {where_sql}
         ORDER BY emp.razao_social
         LIMIT ? OFFSET ?
        """,  # noqa: S608 — where_sql é construído a partir de whitelist
        params,
    )
    return [dict(row) for row in cur]


def contar_empresas_por_cnae(
    conn: sqlite3.Connection,
    cnae: str,
    municipio_codigo: str | None,
    uf: str | None,
) -> int:
    where = ["cnae_fiscal_principal = ?"]
    params: list[Any] = [cnae]
    if municipio_codigo:
        where.append("municipio = ?")
        params.append(municipio_codigo)
    if uf:
        where.append("uf = ?")
        params.append(uf.upper())
    where_sql = " AND ".join(where)
    cur = conn.execute(
        f"SELECT COUNT(*) AS c FROM estabelecimentos WHERE {where_sql}",  # noqa: S608
        params,
    )
    return int(cur.fetchone()["c"])
