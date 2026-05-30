"""Schemas de empresa, estabelecimento, simples e CNPJ completo."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.comum import (
    CodigoDescricao,
    Contato,
    Endereco,
    IdentificacaoCNPJ,
    Paginacao,
)
from app.schemas.socio import Socio


class SituacaoEstabelecimento(BaseModel):
    """Situação cadastral + data + motivo (quando aplicável)."""

    codigo: str
    descricao: str | None = None
    data: str | None = Field(None, description="ISO 8601 (YYYY-MM-DD); None se vazio.")
    motivo: CodigoDescricao | None = None


class Simples(BaseModel):
    opcao_simples: CodigoDescricao
    data_opcao_simples: str | None = None
    data_exclusao_simples: str | None = None
    opcao_mei: CodigoDescricao
    data_opcao_mei: str | None = None
    data_exclusao_mei: str | None = None


class Empresa(BaseModel):
    cnpj_basico: str
    razao_social: str | None = None
    natureza_juridica: CodigoDescricao | None = None
    qualificacao_responsavel: CodigoDescricao | None = None
    porte: CodigoDescricao | None = None
    capital_social: Decimal | None = Field(
        None, description="Capital social em reais (preserva precisão)."
    )
    capital_social_formatado: str | None = Field(None, description="R$ x.xxx.xxx,xx em pt-BR.")
    ente_federativo_responsavel: str | None = None
    simples: Simples | None = None


class Estabelecimento(BaseModel):
    matriz_filial: CodigoDescricao
    nome_fantasia: str | None = None
    situacao: SituacaoEstabelecimento
    data_inicio_atividade: str | None = None
    cnae_principal: CodigoDescricao | None = None
    cnaes_secundarios: list[CodigoDescricao] = Field(default_factory=list)
    endereco: Endereco
    contato: Contato
    situacao_especial: str | None = None
    data_situacao_especial: str | None = None


class SociosResumo(Paginacao):
    """Lista de sócios — caber inline se total <= limit."""

    lista: list[Socio] = Field(default_factory=list)


class EstabelecimentosFiliaisResumo(Paginacao):
    """Sumário; lista completa vem por subrota."""

    pass


class Metadados(BaseModel):
    periodo_dados: str | None = Field(None, description="YYYY-MM da safra ingerida no banco.")
    consultado_em: str = Field(..., description="ISO 8601 timestamp (UTC).")


class CNPJResponse(BaseModel):
    cnpj: IdentificacaoCNPJ
    empresa: Empresa
    estabelecimento: Estabelecimento
    estabelecimentos_filiais: EstabelecimentosFiliaisResumo
    socios: SociosResumo
    metadados: Metadados
