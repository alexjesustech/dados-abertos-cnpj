"""Depends do FastAPI: conexão por request + validação de CNPJ no path."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status

from app.config import Settings, get_settings
from app.db import conectar
from cnpj_lib.formatador import normalizar
from cnpj_lib.validador import validar


def get_settings_dep() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_conn(settings: SettingsDep) -> Iterator[sqlite3.Connection]:
    with conectar(settings.db_path) as conn:
        yield conn


ConnDep = Annotated[sqlite3.Connection, Depends(get_conn)]


def validar_cnpj_path(
    cnpj: Annotated[str, Path(description="CNPJ com 14 chars (num ou alfa), com ou sem máscara.")],
) -> str:
    """Valida CNPJ no path e devolve forma normalizada (sem máscara, maiúscula)."""
    if not validar(cnpj):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"CNPJ inválido: {cnpj!r}",
        )
    return normalizar(cnpj)


def validar_basico_path(
    cnpj_basico: Annotated[str, Path(description="Base de 8 chars do CNPJ (sem ordem nem DV).")],
) -> str:
    """Aceita basico de 8 chars normalizados em [0-9A-Z]."""
    base = normalizar(cnpj_basico)
    if len(base) != 8 or not all(c.isdigit() or "A" <= c <= "Z" for c in base):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"cnpj_basico inválido: esperado 8 chars [0-9A-Z], recebido {cnpj_basico!r}",
        )
    return base


CNPJValidado = Annotated[str, Depends(validar_cnpj_path)]
BasicoValidado = Annotated[str, Depends(validar_basico_path)]
