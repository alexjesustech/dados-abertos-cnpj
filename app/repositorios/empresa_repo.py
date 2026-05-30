"""SELECTs nas tabelas `empresas` e `simples` (PK = cnpj_basico em ambas)."""

from __future__ import annotations

import sqlite3
from typing import Any


def buscar_empresa(conn: sqlite3.Connection, cnpj_basico: str) -> dict[str, Any] | None:
    cur = conn.execute(
        """
        SELECT cnpj_basico, razao_social, natureza_juridica, qualificacao_responsavel,
               capital_social, porte_empresa, ente_federativo_responsavel
          FROM empresas
         WHERE cnpj_basico = ?
        """,
        (cnpj_basico,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def buscar_simples(conn: sqlite3.Connection, cnpj_basico: str) -> dict[str, Any] | None:
    cur = conn.execute(
        """
        SELECT cnpj_basico, opcao_pelo_simples, data_opcao_simples, data_exclusao_simples,
               opcao_pelo_mei, data_opcao_mei, data_exclusao_mei
          FROM simples
         WHERE cnpj_basico = ?
        """,
        (cnpj_basico,),
    )
    row = cur.fetchone()
    return dict(row) if row else None
