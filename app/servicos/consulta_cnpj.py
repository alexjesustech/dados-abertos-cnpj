"""Serviço que monta CNPJResponse completo joinando repos + lookups + domínio.

É o ponto de reuso entre rotas HTTP e tools MCP — nenhuma rota nem tool deve
falar com repos diretamente.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.repositorios import empresa_repo, estabelecimento_repo, socio_repo
from app.repositorios.lookup_repo import LookupCache
from app.schemas.cnpj import (
    CNPJResponse,
    Empresa,
    Estabelecimento,
    EstabelecimentosFiliaisResumo,
    Metadados,
    Simples,
    SituacaoEstabelecimento,
    SociosResumo,
)
from app.schemas.comum import (
    CodigoDescricao,
    Contato,
    Documento,
    Endereco,
    IdentificacaoCNPJ,
    PartesCNPJ,
    Telefone,
)
from app.schemas.socio import RepresentanteLegal, Socio
from cnpj_lib import dominio
from cnpj_lib.formatador import formatar, fragmentar, parsear_data_yyyymmdd
from cnpj_lib.validador import eh_alfanumerico


class CNPJNaoEncontrado(Exception):  # noqa: N818
    """Raised quando empresa+estabelecimento não existem no banco."""


# ============================ HELPERS DE TRADUÇÃO ============================


def _cd_lookup(lookups: LookupCache, tabela: str, codigo: str | None) -> CodigoDescricao | None:
    if codigo is None or codigo == "":
        return None
    return CodigoDescricao(codigo=str(codigo), descricao=lookups.descricao(tabela, codigo))


def _cd_dominio(tabela: str, codigo: str | None) -> CodigoDescricao | None:
    if codigo is None or codigo == "":
        return None
    return CodigoDescricao(codigo=str(codigo), descricao=dominio.descrever(tabela, str(codigo)))


def _telefone(ddd: str | None, numero: str | None) -> Telefone | None:
    if not ddd and not numero:
        return None
    return Telefone(ddd=ddd or None, numero=numero or None)


def _parse_capital(s: str | None) -> tuple[Decimal | None, str | None]:
    """Devolve (Decimal, str formatada pt-BR) ou (None, None) se inválido."""
    if s is None or s == "":
        return None, None
    txt = str(s).replace(",", ".")
    try:
        valor = Decimal(txt)
    except (InvalidOperation, ValueError):
        return None, None
    inteiro, _, decimal = f"{valor:.2f}".partition(".")
    grupos = []
    while inteiro:
        grupos.append(inteiro[-3:])
        inteiro = inteiro[:-3]
    formatado = "R$ " + ".".join(reversed(grupos)) + "," + decimal
    return valor, formatado


def _cnaes_secundarios(lookups: LookupCache, raw: str | None) -> list[CodigoDescricao]:
    if not raw:
        return []
    out: list[CodigoDescricao] = []
    for token in raw.split(","):
        codigo = token.strip()
        if codigo:
            out.append(CodigoDescricao(codigo=codigo, descricao=lookups.descricao("cnaes", codigo)))
    return out


# ============================== MONTADORES ===================================


def _montar_simples(linha: dict[str, Any] | None) -> Simples | None:
    if linha is None:
        return None
    return Simples(
        opcao_simples=_cd_dominio("opcao_simples", linha.get("opcao_pelo_simples"))
        or CodigoDescricao(codigo="?", descricao=None),
        data_opcao_simples=parsear_data_yyyymmdd(linha.get("data_opcao_simples")),
        data_exclusao_simples=parsear_data_yyyymmdd(linha.get("data_exclusao_simples")),
        opcao_mei=_cd_dominio("opcao_simples", linha.get("opcao_pelo_mei"))
        or CodigoDescricao(codigo="?", descricao=None),
        data_opcao_mei=parsear_data_yyyymmdd(linha.get("data_opcao_mei")),
        data_exclusao_mei=parsear_data_yyyymmdd(linha.get("data_exclusao_mei")),
    )


def _montar_empresa(
    linha: dict[str, Any],
    simples_linha: dict[str, Any] | None,
    lookups: LookupCache,
) -> Empresa:
    capital, capital_fmt = _parse_capital(linha.get("capital_social"))
    return Empresa(
        cnpj_basico=linha["cnpj_basico"],
        razao_social=linha.get("razao_social"),
        natureza_juridica=_cd_lookup(lookups, "naturezas", linha.get("natureza_juridica")),
        qualificacao_responsavel=_cd_lookup(
            lookups, "qualificacoes", linha.get("qualificacao_responsavel")
        ),
        porte=_cd_dominio("porte_empresa", linha.get("porte_empresa")),
        capital_social=capital,
        capital_social_formatado=capital_fmt,
        ente_federativo_responsavel=linha.get("ente_federativo_responsavel") or None,
        simples=_montar_simples(simples_linha),
    )


def _montar_estabelecimento(linha: dict[str, Any], lookups: LookupCache) -> Estabelecimento:
    return Estabelecimento(
        matriz_filial=_cd_dominio(
            "identificador_matriz_filial", linha.get("identificador_matriz_filial")
        )
        or CodigoDescricao(codigo="?", descricao=None),
        nome_fantasia=linha.get("nome_fantasia") or None,
        situacao=SituacaoEstabelecimento(
            codigo=str(linha.get("situacao_cadastral") or ""),
            descricao=dominio.descrever(
                "situacao_cadastral", str(linha.get("situacao_cadastral") or "")
            ),
            data=parsear_data_yyyymmdd(linha.get("data_situacao_cadastral")),
            motivo=_cd_lookup(lookups, "motivos", linha.get("motivo_situacao_cadastral")),
        ),
        data_inicio_atividade=parsear_data_yyyymmdd(linha.get("data_inicio_atividade")),
        cnae_principal=_cd_lookup(lookups, "cnaes", linha.get("cnae_fiscal_principal")),
        cnaes_secundarios=_cnaes_secundarios(lookups, linha.get("cnae_fiscal_secundaria")),
        endereco=Endereco(
            tipo_logradouro=linha.get("tipo_logradouro") or None,
            logradouro=linha.get("logradouro") or None,
            numero=linha.get("numero") or None,
            complemento=linha.get("complemento") or None,
            bairro=linha.get("bairro") or None,
            cep=linha.get("cep") or None,
            uf=linha.get("uf") or None,
            municipio=_cd_lookup(lookups, "municipios", linha.get("municipio")),
            pais=_cd_lookup(lookups, "paises", linha.get("pais")),
            nome_cidade_exterior=linha.get("nome_cidade_exterior") or None,
        ),
        contato=Contato(
            telefone_1=_telefone(linha.get("ddd_1"), linha.get("telefone_1")),
            telefone_2=_telefone(linha.get("ddd_2"), linha.get("telefone_2")),
            fax=_telefone(linha.get("ddd_fax"), linha.get("fax")),
            email=linha.get("correio_eletronico") or None,
        ),
        situacao_especial=linha.get("situacao_especial") or None,
        data_situacao_especial=parsear_data_yyyymmdd(linha.get("data_situacao_especial")),
    )


def _montar_socio(linha: dict[str, Any], lookups: LookupCache) -> Socio:
    ident = str(linha.get("identificador_socio") or "")
    doc_raw = linha.get("cnpj_cpf_socio") or ""
    # 1 = PJ, 2 = PF, 3 = Estrangeiro
    if ident == "1":
        doc = Documento(valor=doc_raw, tipo="cnpj", mascarado=False)
    else:
        doc = Documento(valor=doc_raw, tipo="cpf", mascarado=True)

    representante = None
    rep_doc = linha.get("representante_legal")
    if rep_doc:
        representante = RepresentanteLegal(
            documento=Documento(valor=rep_doc, tipo="cpf", mascarado=True),
            nome=linha.get("nome_do_representante") or None,
            qualificacao=_cd_lookup(
                lookups, "qualificacoes", linha.get("qualificacao_representante_legal")
            ),
        )

    return Socio(
        identificador=_cd_dominio("identificador_socio", ident)
        or CodigoDescricao(codigo=ident, descricao=None),
        nome_razao_social=linha.get("nome_socio_razao_social") or None,
        documento=doc,
        qualificacao=_cd_lookup(lookups, "qualificacoes", linha.get("qualificacao_socio")),
        data_entrada=parsear_data_yyyymmdd(linha.get("data_entrada_sociedade")),
        pais=_cd_lookup(lookups, "paises", linha.get("pais")),
        faixa_etaria=_cd_dominio("faixa_etaria", linha.get("faixa_etaria")),
        representante_legal=representante,
    )


# ============================ ORQUESTRADOR ===================================


def montar_cnpj_completo(
    conn: sqlite3.Connection,
    cnpj14: str,
    lookups: LookupCache,
    *,
    socios_limite: int = 50,
    periodo_dados: str | None = None,
) -> CNPJResponse:
    """Monta o payload completo para o CNPJ informado.

    Args:
        conn: conexão SQLite read-only.
        cnpj14: CNPJ normalizado (14 chars, sem máscara, upper).
        lookups: cache de lookups já carregado.
        socios_limite: quantos sócios incluir inline (paginação real via subrota).
        periodo_dados: YYYY-MM da safra ingerida (para metadados).

    Raises:
        CNPJNaoEncontrado: se o estabelecimento específico não existe.
    """
    basico, ordem, dv = fragmentar(cnpj14)

    empresa_linha = empresa_repo.buscar_empresa(conn, basico)
    estab_linha = estabelecimento_repo.buscar(conn, basico, ordem, dv)
    if empresa_linha is None or estab_linha is None:
        raise CNPJNaoEncontrado(cnpj14)

    simples_linha = empresa_repo.buscar_simples(conn, basico)
    total_filiais = estabelecimento_repo.contar_estabelecimentos(conn, basico)
    total_socios = socio_repo.contar_socios(conn, basico)
    socios_linhas = socio_repo.listar_por_basico(conn, basico, socios_limite, 0)

    socios = [_montar_socio(linha, lookups) for linha in socios_linhas]

    return CNPJResponse(
        cnpj=IdentificacaoCNPJ(
            completo=cnpj14,
            formatado=formatar(cnpj14),
            partes=PartesCNPJ(basico=basico, ordem=ordem, dv=dv),
            alfanumerico=eh_alfanumerico(cnpj14),
        ),
        empresa=_montar_empresa(empresa_linha, simples_linha, lookups),
        estabelecimento=_montar_estabelecimento(estab_linha, lookups),
        estabelecimentos_filiais=EstabelecimentosFiliaisResumo(
            total=total_filiais,
            retornados=1,  # a matriz/filial específica já vem no objeto principal
            tem_mais=total_filiais > 1,
            link=f"/cnpj/{basico}/estabelecimentos" if total_filiais > 1 else None,
        ),
        socios=SociosResumo(
            total=total_socios,
            retornados=len(socios),
            tem_mais=total_socios > len(socios),
            link=f"/cnpj/{basico}/socios" if total_socios > len(socios) else None,
            lista=socios,
        ),
        metadados=Metadados(
            periodo_dados=periodo_dados,
            consultado_em=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        ),
    )


def listar_socios_paginados(
    conn: sqlite3.Connection,
    cnpj_basico: str,
    lookups: LookupCache,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Socio], int]:
    """Lista paginada para a subrota /cnpj/{basico}/socios."""
    total = socio_repo.contar_socios(conn, cnpj_basico)
    linhas = socio_repo.listar_por_basico(conn, cnpj_basico, limit, offset)
    return [_montar_socio(linha, lookups) for linha in linhas], total


def listar_estabelecimentos_paginados(
    conn: sqlite3.Connection,
    cnpj_basico: str,
    lookups: LookupCache,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Estabelecimento], int]:
    """Lista paginada para a subrota /cnpj/{basico}/estabelecimentos."""
    total = estabelecimento_repo.contar_estabelecimentos(conn, cnpj_basico)
    linhas = estabelecimento_repo.listar_por_basico(conn, cnpj_basico, limit, offset)
    return [_montar_estabelecimento(linha, lookups) for linha in linhas], total
