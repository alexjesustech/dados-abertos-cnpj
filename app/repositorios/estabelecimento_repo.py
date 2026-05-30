"""SELECTs na tabela `estabelecimentos` (PK = basico + ordem + dv)."""

from __future__ import annotations

import sqlite3
from typing import Any

_COLUNAS = """
    cnpj_basico, cnpj_ordem, cnpj_dv,
    identificador_matriz_filial, nome_fantasia,
    situacao_cadastral, data_situacao_cadastral, motivo_situacao_cadastral,
    nome_cidade_exterior, pais, data_inicio_atividade,
    cnae_fiscal_principal, cnae_fiscal_secundaria,
    tipo_logradouro, logradouro, numero, complemento, bairro, cep,
    uf, municipio,
    ddd_1, telefone_1, ddd_2, telefone_2, ddd_fax, fax,
    correio_eletronico,
    situacao_especial, data_situacao_especial
"""


def buscar(
    conn: sqlite3.Connection,
    cnpj_basico: str,
    cnpj_ordem: str,
    cnpj_dv: str,
) -> dict[str, Any] | None:
    """Estabelecimento específico (matriz ou filial concreta)."""
    cur = conn.execute(
        f"""
        SELECT {_COLUNAS}
          FROM estabelecimentos
         WHERE cnpj_basico = ? AND cnpj_ordem = ? AND cnpj_dv = ?
        """,
        (cnpj_basico, cnpj_ordem, cnpj_dv),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def matriz_de(conn: sqlite3.Connection, cnpj_basico: str) -> dict[str, Any] | None:
    """Devolve a matriz (identificador_matriz_filial = '1') do CNPJ base."""
    cur = conn.execute(
        f"""
        SELECT {_COLUNAS}
          FROM estabelecimentos
         WHERE cnpj_basico = ? AND identificador_matriz_filial = '1'
         LIMIT 1
        """,
        (cnpj_basico,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def contar_estabelecimentos(conn: sqlite3.Connection, cnpj_basico: str) -> int:
    cur = conn.execute(
        "SELECT COUNT(*) AS c FROM estabelecimentos WHERE cnpj_basico = ?",
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
          FROM estabelecimentos
         WHERE cnpj_basico = ?
         ORDER BY cnpj_ordem
         LIMIT ? OFFSET ?
        """,
        (cnpj_basico, limit, offset),
    )
    return [dict(row) for row in cur]
