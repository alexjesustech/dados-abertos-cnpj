"""Modelos Pydantic compartilhados — usados pela API HTTP e pelas tools MCP."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CodigoDescricao(BaseModel):
    """Par código + descrição traduzida (de tabela lookup ou domínio hardcoded)."""

    codigo: str = Field(..., description="Código original como vem da RFB.")
    descricao: str | None = Field(
        None, description="Descrição humana (pode ser nula se código desconhecido)."
    )


class PartesCNPJ(BaseModel):
    basico: str = Field(..., min_length=8, max_length=8)
    ordem: str = Field(..., min_length=4, max_length=4)
    dv: str = Field(..., min_length=2, max_length=2)


class IdentificacaoCNPJ(BaseModel):
    completo: str = Field(..., description="14 caracteres normalizados, sem máscara.")
    formatado: str = Field(..., description="Com máscara XX.XXX.XXX/XXXX-DD.")
    partes: PartesCNPJ
    alfanumerico: bool = Field(..., description="True se base de 12 tem ao menos uma letra.")


class Telefone(BaseModel):
    ddd: str | None = None
    numero: str | None = None


class Endereco(BaseModel):
    tipo_logradouro: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cep: str | None = None
    uf: str | None = None
    municipio: CodigoDescricao | None = None
    pais: CodigoDescricao | None = None
    nome_cidade_exterior: str | None = None


class Contato(BaseModel):
    telefone_1: Telefone | None = None
    telefone_2: Telefone | None = None
    fax: Telefone | None = None
    email: str | None = None


class Documento(BaseModel):
    valor: str = Field(..., description="CPF mascarado ('***NNNNNN**') ou CNPJ de 14 chars.")
    tipo: Literal["cpf", "cnpj"]
    mascarado: bool = Field(
        ..., description="True se o valor está mascarado (sempre true para PF)."
    )


class Paginacao(BaseModel):
    total: int = Field(..., ge=0, description="Quantidade total disponível no banco.")
    retornados: int = Field(..., ge=0, description="Quantos itens vieram neste payload.")
    tem_mais: bool = Field(..., description="True se há mais itens além dos retornados.")
    link: str | None = Field(
        None, description="Subrota para listagem completa, quando o array foi omitido."
    )


class ErroResponse(BaseModel):
    detalhe: str
    codigo: str | None = None
