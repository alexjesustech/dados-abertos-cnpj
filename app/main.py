"""Entrypoint FastAPI da Caixa-preta de CNPJ.

Levantar:
    uv run cnpj-api
ou:
    uv run uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import conectar
from app.repositorios.lookup_repo import carregar_lookups
from app.rotas import cnpj as rotas_cnpj
from app.rotas import meta as rotas_meta


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Carrega cache de lookups e detecta período atual no startup."""
    settings = get_settings()
    with conectar(settings.db_path) as conn:
        app.state.lookups = carregar_lookups(conn)
        cur = conn.execute(
            "SELECT SUBSTR(MAX(data_importacao), 1, 7) AS periodo FROM controle_importacao"
        )
        row = cur.fetchone()
        app.state.periodo_dados = row["periodo"] if row else None
    # stats_cache é populado lazy no primeiro hit (COUNT é caro sem ANALYZE)
    app.state.stats_cache = None
    yield
    # nada a desfazer — conexões são por-request


def criar_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Dados Abertos CNPJ — API local",
        description=(
            "Espelho local read-only da RFB. Sem rate-limit, sem auth — uso pessoal. "
            "Suporta CNPJ numérico (legado) e alfanumérico (NT Conjunta 2025.001, vigência 06/07/2026)."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(rotas_meta.router, prefix="/api/v1")
    app.include_router(rotas_cnpj.router, prefix="/api/v1")
    return app


app = criar_app()


def run_uvicorn() -> None:
    """Entrypoint para o script `cnpj-api` (registrado em pyproject.toml)."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_bind,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    run_uvicorn()
