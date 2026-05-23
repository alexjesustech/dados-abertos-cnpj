"""Rotas /cnpj/{cnpj} e subrotas /socios e /estabelecimentos."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.dependencias import BasicoValidado, CNPJValidado, ConnDep
from app.schemas.cnpj import CNPJResponse, SociosResumo
from app.schemas.cnpj import EstabelecimentosFiliaisResumo
from app.servicos.consulta_cnpj import (
    CNPJNaoEncontrado,
    listar_estabelecimentos_paginados,
    listar_socios_paginados,
    montar_cnpj_completo,
)

router = APIRouter(tags=["cnpj"])


@router.get(
    "/cnpj/{cnpj}",
    response_model=CNPJResponse,
    summary="Dados completos de um CNPJ específico",
    response_model_exclude_none=False,
)
def consultar_cnpj(
    request: Request,
    cnpj: CNPJValidado,
    conn: ConnDep,
    socios_limite: int = Query(50, ge=1, le=500, description="Quantos sócios incluir inline."),
) -> CNPJResponse:
    """Devolve empresa + simples + estabelecimento + sócios (inline ou subrota)."""
    lookups = request.app.state.lookups
    periodo = request.app.state.periodo_dados
    try:
        return montar_cnpj_completo(
            conn,
            cnpj14=cnpj,
            lookups=lookups,
            socios_limite=socios_limite,
            periodo_dados=periodo,
        )
    except CNPJNaoEncontrado as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"CNPJ {cnpj} não encontrado.") from exc


@router.get(
    "/cnpj/{cnpj_basico}/socios",
    response_model=SociosResumo,
    summary="Sócios paginados de um CNPJ base",
)
def listar_socios(
    request: Request,
    cnpj_basico: BasicoValidado,
    conn: ConnDep,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> SociosResumo:
    lookups = request.app.state.lookups
    lista, total = listar_socios_paginados(conn, cnpj_basico, lookups, limit=limit, offset=offset)
    return SociosResumo(
        total=total,
        retornados=len(lista),
        tem_mais=offset + len(lista) < total,
        link=None,
        lista=lista,
    )


@router.get(
    "/cnpj/{cnpj_basico}/estabelecimentos",
    response_model=EstabelecimentosFiliaisResumo,
    summary="Estabelecimentos paginados (sem corpo — só sumário; corpo via /cnpj/{cnpj_completo})",
)
def listar_estabelecimentos(
    request: Request,
    cnpj_basico: BasicoValidado,
    conn: ConnDep,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> EstabelecimentosFiliaisResumo:
    lookups = request.app.state.lookups
    lista, total = listar_estabelecimentos_paginados(
        conn, cnpj_basico, lookups, limit=limit, offset=offset
    )
    return EstabelecimentosFiliaisResumo(
        total=total,
        retornados=len(lista),
        tem_mais=offset + len(lista) < total,
        link=None,
    )
