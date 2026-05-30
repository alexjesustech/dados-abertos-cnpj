"""Configuração via env (Pydantic Settings)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_path: Path = Field(
        default=ROOT / "dados_cnpj.db", description="Caminho do SQLite com dados ingeridos."
    )
    api_bind: str = Field(
        default="127.0.0.1", description="Endereço de bind do uvicorn (padrão local-only)."
    )
    api_port: int = Field(default=8000)
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost", "http://127.0.0.1"]
    )

    socio_pagina_default: int = Field(default=50, ge=1, le=500)
    estab_pagina_default: int = Field(default=50, ge=1, le=500)
    lista_pagina_max: int = Field(default=500, ge=1, le=2000)


def get_settings() -> Settings:
    """Factory cacheada (ler Settings em runtime, não importar global)."""
    return Settings()
