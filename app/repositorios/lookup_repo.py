"""Repositório das 6 tabelas lookup (cnaes, municipios, naturezas, ...).

Carrega todas no startup da API em dicionários de memória. Tamanho fixo
conhecido (~200k entradas no total, ~30 MB RAM). Após carregado, traduções
são O(1) e zero hit no SQLite.
"""

from __future__ import annotations

import sqlite3
from typing import Final

TABELAS_LOOKUP: Final[tuple[str, ...]] = (
    "cnaes",
    "motivos",
    "municipios",
    "paises",
    "qualificacoes",
    "naturezas",
)


class LookupCache:
    """Cache em memória dos 6 lookups da RFB."""

    def __init__(self, mapas: dict[str, dict[str, str]]) -> None:
        self._mapas = mapas

    def descricao(self, tabela: str, codigo: str | None) -> str | None:
        if codigo is None:
            return None
        mapa = self._mapas.get(tabela)
        if mapa is None:
            return None
        return mapa.get(str(codigo))

    def tabela(self, tabela: str) -> dict[str, str]:
        return self._mapas.get(tabela, {})

    def contagem(self) -> dict[str, int]:
        return {nome: len(mapa) for nome, mapa in self._mapas.items()}


def carregar_lookups(conn: sqlite3.Connection) -> LookupCache:
    """Lê as 6 tabelas lookup e devolve o cache pronto."""
    mapas: dict[str, dict[str, str]] = {}
    for nome in TABELAS_LOOKUP:
        cur = conn.execute(f"SELECT codigo, descricao FROM {nome}")  # noqa: S608 — nome whitelist
        mapas[nome] = {str(row["codigo"]): row["descricao"] for row in cur}
    return LookupCache(mapas)
