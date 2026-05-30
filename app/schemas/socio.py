"""Schemas de sócio e representante legal."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.comum import CodigoDescricao, Documento


class RepresentanteLegal(BaseModel):
    documento: Documento
    nome: str | None = Field(None, description="97% dos registros vêm nulo na RFB.")
    qualificacao: CodigoDescricao | None = None


class Socio(BaseModel):
    identificador: CodigoDescricao = Field(..., description="1=PJ, 2=PF, 3=Estrangeiro.")
    nome_razao_social: str | None = None
    documento: Documento
    qualificacao: CodigoDescricao | None = None
    data_entrada: str | None = Field(None, description="ISO 8601 (YYYY-MM-DD); None se vazio.")
    pais: CodigoDescricao | None = None
    faixa_etaria: CodigoDescricao | None = Field(
        None, description="Apenas para PF; 'Não se aplica' para PJ."
    )
    representante_legal: RepresentanteLegal | None = None
