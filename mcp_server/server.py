"""Servidor MCP para Dados Abertos do CNPJ.

Expõe 9 ferramentas tipadas que reusam a camada `app.servicos` da API
HTTP (sem rede, sem subprocess — chamada Python direta). Cada tool de
listagem é paginada manualmente (MCP não tem paginação nativa) com
``limit/offset`` + metadado ``tem_mais``.

Levantar (stdio default, padrão Claude Code):
    uv run mcp-cnpj

Registrar em ~/.claude/mcp.json (não fazemos automaticamente — usuário
controla):
    {
      "mcpServers": {
        "cnpj-br": {
          "command": "uv",
          "args": ["--directory", "/home/sander/projects/dados-abertos-cnpj",
                   "run", "mcp-cnpj"]
        }
      }
    }
"""
from __future__ import annotations

from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import conectar
from app.repositorios import (
    busca_repo,
    controle_repo,
    socio_repo,
)
from app.repositorios.lookup_repo import LookupCache, carregar_lookups
from app.servicos.consulta_cnpj import (
    CNPJNaoEncontrado,
    listar_estabelecimentos_paginados,
    listar_socios_paginados,
    montar_cnpj_completo,
)
from cnpj_lib import dominio
from cnpj_lib.formatador import normalizar
from cnpj_lib.validador import eh_alfanumerico, validar

mcp = FastMCP("cnpj-br")


# ============================ CACHE GLOBAL ===================================
# Lookups carregados na primeira tool call (mantém startup do MCP rápido).

_lookups_cache: LookupCache | None = None
_periodo_cache: str | None = None


def _lookups() -> LookupCache:
    global _lookups_cache, _periodo_cache
    if _lookups_cache is None:
        settings = get_settings()
        with conectar(settings.db_path) as conn:
            _lookups_cache = carregar_lookups(conn)
            cur = conn.execute(
                "SELECT SUBSTR(MAX(data_importacao), 1, 7) AS periodo FROM controle_importacao"
            )
            row = cur.fetchone()
            _periodo_cache = row["periodo"] if row else None
    return _lookups_cache


# ============================ MODELS DE I/O ==================================

class Pagina(BaseModel):
    """Sumário de paginação comum a todas as tools que listam."""
    total: int
    retornados: int
    tem_mais: bool


class ResumoSocio(BaseModel):
    cnpj_basico: str
    identificador: dict[str, str | None]  # codigo + descricao
    nome_razao_social: str | None
    documento: str
    qualificacao: dict[str, str | None] | None


class ResumoEmpresaPorCnae(BaseModel):
    cnpj_basico: str
    cnpj_ordem: str
    cnpj_dv: str
    razao_social: str | None
    situacao_cadastral: dict[str, str | None]
    municipio: dict[str, str | None] | None
    uf: str | None


class ResumoCnaeAgregado(BaseModel):
    cnae: dict[str, str | None]
    total_estabelecimentos: int


class PeriodoImportado(BaseModel):
    periodo: str
    arquivos: int
    ultima_data: str


# ============================ HELPERS ========================================

def _cd(tabela: str, codigo: str | None, *, lookup: bool = True) -> dict[str, str | None]:
    """Devolve dict {codigo, descricao} pra serialização compacta nas tools."""
    if codigo is None or codigo == "":
        return {"codigo": "", "descricao": None}
    if lookup:
        desc = _lookups().descricao(tabela, codigo)
    else:
        desc = dominio.descrever(tabela, str(codigo)) if tabela in dominio.TABELAS else None
    return {"codigo": str(codigo), "descricao": desc}


def _pagina(total: int, retornados: int, offset: int) -> Pagina:
    return Pagina(total=total, retornados=retornados, tem_mais=(offset + retornados) < total)


# ============================ TOOLS ==========================================

@mcp.tool(description="Devolve dados completos de um CNPJ (numérico legado ou alfanumérico).")
def buscar_empresa(
    cnpj: Annotated[str, Field(description="CNPJ de 14 chars, com ou sem máscara.")],
    socios_limite: Annotated[int, Field(default=20, ge=1, le=200,
                                        description="Quantos sócios incluir inline.")] = 20,
) -> dict[str, Any]:
    if not validar(cnpj):
        raise ValueError(f"CNPJ inválido: {cnpj!r}")
    cnpj14 = normalizar(cnpj)
    settings = get_settings()
    with conectar(settings.db_path) as conn:
        lookups = _lookups()
        try:
            resp = montar_cnpj_completo(
                conn, cnpj14=cnpj14, lookups=lookups,
                socios_limite=socios_limite, periodo_dados=_periodo_cache,
            )
        except CNPJNaoEncontrado as exc:
            raise ValueError(f"CNPJ {cnpj14} não encontrado.") from exc
    return resp.model_dump(mode="json")


@mcp.tool(description="Lista sócios paginados de um CNPJ base (8 chars).")
def listar_socios(
    cnpj_basico: Annotated[str, Field(description="Base do CNPJ — primeiros 8 chars.")],
    limit: Annotated[int, Field(default=50, ge=1, le=500)] = 50,
    offset: Annotated[int, Field(default=0, ge=0)] = 0,
) -> dict[str, Any]:
    basico = normalizar(cnpj_basico)
    if len(basico) != 8:
        raise ValueError(f"cnpj_basico deve ter 8 chars; recebido {cnpj_basico!r}")
    settings = get_settings()
    with conectar(settings.db_path) as conn:
        lookups = _lookups()
        lista, total = listar_socios_paginados(conn, basico, lookups, limit=limit, offset=offset)
    return {
        "pagina": _pagina(total, len(lista), offset).model_dump(),
        "socios": [s.model_dump(mode="json") for s in lista],
    }


@mcp.tool(description="Lista filiais/estabelecimentos paginados de um CNPJ base.")
def listar_filiais(
    cnpj_basico: Annotated[str, Field(description="Base do CNPJ — primeiros 8 chars.")],
    limit: Annotated[int, Field(default=50, ge=1, le=500)] = 50,
    offset: Annotated[int, Field(default=0, ge=0)] = 0,
) -> dict[str, Any]:
    basico = normalizar(cnpj_basico)
    if len(basico) != 8:
        raise ValueError(f"cnpj_basico deve ter 8 chars; recebido {cnpj_basico!r}")
    settings = get_settings()
    with conectar(settings.db_path) as conn:
        lookups = _lookups()
        lista, total = listar_estabelecimentos_paginados(
            conn, basico, lookups, limit=limit, offset=offset,
        )
    return {
        "pagina": _pagina(total, len(lista), offset).model_dump(),
        "estabelecimentos": [e.model_dump(mode="json") for e in lista],
    }


@mcp.tool(description="Empresas onde o documento aparece como sócio. CPF mascarado: ***NNNNNN**.")
def vinculos_pj(
    documento: Annotated[str, Field(description="CPF mascarado padrão RFB ou CNPJ de 14 chars.")],
    limit: Annotated[int, Field(default=50, ge=1, le=500)] = 50,
    offset: Annotated[int, Field(default=0, ge=0)] = 0,
) -> dict[str, Any]:
    settings = get_settings()
    with conectar(settings.db_path) as conn:
        total = socio_repo.contar_por_documento(conn, documento)
        rows = socio_repo.listar_por_documento(conn, documento, limit, offset)
        lookups = _lookups()
        socios_out = [
            ResumoSocio(
                cnpj_basico=r["cnpj_basico"],
                identificador=_cd("identificador_socio", r.get("identificador_socio"), lookup=False),
                nome_razao_social=r.get("nome_socio_razao_social"),
                documento=r.get("cnpj_cpf_socio") or "",
                qualificacao=_cd("qualificacoes", r.get("qualificacao_socio")),
            ).model_dump()
            for r in rows
        ]
    return {
        "pagina": _pagina(total, len(socios_out), offset).model_dump(),
        "vinculos": socios_out,
    }


@mcp.tool(description="Top CNAEs por contagem de estabelecimentos em um município (código RFB).")
def cnaes_por_municipio(
    municipio_codigo: Annotated[str, Field(description="Código RFB do município (ver lookup `municipios`).")],
    limit: Annotated[int, Field(default=50, ge=1, le=500)] = 50,
    offset: Annotated[int, Field(default=0, ge=0)] = 0,
) -> dict[str, Any]:
    settings = get_settings()
    with conectar(settings.db_path) as conn:
        rows = busca_repo.cnaes_por_municipio(conn, municipio_codigo, limit, offset)
        total = busca_repo.contar_cnaes_por_municipio(conn, municipio_codigo)
        lookups = _lookups()
        agg = [
            ResumoCnaeAgregado(
                cnae=_cd("cnaes", r["cnae"]),
                total_estabelecimentos=int(r["total"]),
            ).model_dump()
            for r in rows
        ]
    return {
        "pagina": _pagina(total, len(agg), offset).model_dump(),
        "municipio_codigo": municipio_codigo,
        "municipio": lookups.descricao("municipios", municipio_codigo),
        "cnaes": agg,
    }


@mcp.tool(description="Empresas por CNAE principal, opcionalmente filtradas por município/UF.")
def empresas_por_cnae(
    cnae: Annotated[str, Field(description="Código CNAE de 7 dígitos (ver lookup `cnaes`).")],
    municipio_codigo: Annotated[str | None, Field(default=None)] = None,
    uf: Annotated[str | None, Field(default=None, description="Sigla UF, 2 chars.")] = None,
    limit: Annotated[int, Field(default=50, ge=1, le=500)] = 50,
    offset: Annotated[int, Field(default=0, ge=0)] = 0,
) -> dict[str, Any]:
    settings = get_settings()
    with conectar(settings.db_path) as conn:
        rows = busca_repo.empresas_por_cnae(conn, cnae, municipio_codigo, uf, limit, offset)
        total = busca_repo.contar_empresas_por_cnae(conn, cnae, municipio_codigo, uf)
        lookups = _lookups()
        empresas = [
            ResumoEmpresaPorCnae(
                cnpj_basico=r["cnpj_basico"],
                cnpj_ordem=r["cnpj_ordem"],
                cnpj_dv=r["cnpj_dv"],
                razao_social=r.get("razao_social"),
                situacao_cadastral=_cd("situacao_cadastral", r.get("situacao_cadastral"), lookup=False),
                municipio=_cd("municipios", r.get("municipio")),
                uf=r.get("uf"),
            ).model_dump()
            for r in rows
        ]
    return {
        "pagina": _pagina(total, len(empresas), offset).model_dump(),
        "cnae": {"codigo": cnae, "descricao": lookups.descricao("cnaes", cnae)},
        "empresas": empresas,
    }


@mcp.tool(description="Metadados das safras mensais ingeridas (MVP — não calcula diff real).")
def delta_mensal() -> dict[str, Any]:
    """No MVP devolve só metadados de `controle_importacao` por período.

    Para diff real (CNPJs novos/baixados entre safras) precisaria preservar
    snapshots históricos — está no backlog do Caminho 02.
    """
    settings = get_settings()
    with conectar(settings.db_path) as conn:
        periodos = controle_repo.listar_periodos(conn)
    return {
        "periodos": [
            PeriodoImportado(**p).model_dump() for p in periodos
        ],
        "aviso": (
            "MVP: diff real entre safras exige snapshots históricos. "
            "Por enquanto só metadados da controle_importacao."
        ),
    }


@mcp.tool(description="Valida formato e DVs de um CNPJ (numérico ou alfanumérico).")
def validar_cnpj(
    cnpj: Annotated[str, Field(description="CNPJ com ou sem máscara, qualquer caixa.")],
) -> dict[str, Any]:
    ok = validar(cnpj)
    return {
        "cnpj": cnpj,
        "valido": ok,
        "alfanumerico": eh_alfanumerico(cnpj) if ok else False,
    }


@mcp.tool(description="Descrição humana de um código (de lookup RFB ou tabela de domínio hardcoded).")
def descrever_codigo(
    tabela: Annotated[str, Field(description=(
        "Lookup: cnaes|motivos|municipios|paises|qualificacoes|naturezas. "
        "Domínio: situacao_cadastral|identificador_socio|faixa_etaria|"
        "identificador_matriz_filial|opcao_simples|porte_empresa."
    ))],
    codigo: Annotated[str, Field(description="Código original da RFB.")],
) -> dict[str, str | None]:
    if tabela in dominio.TABELAS:
        return {"tabela": tabela, "codigo": codigo, "descricao": dominio.descrever(tabela, codigo)}
    return {"tabela": tabela, "codigo": codigo, "descricao": _lookups().descricao(tabela, codigo)}


# ============================ ENTRYPOINT =====================================

def main() -> None:
    """Roda servidor MCP stdio (chamado pelo entrypoint `mcp-cnpj`)."""
    mcp.run()


if __name__ == "__main__":
    main()
