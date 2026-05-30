"""Testes de cnpj_lib.dominio — tabelas hardcoded da RFB."""

from __future__ import annotations

import pytest

from cnpj_lib.dominio import (
    FAIXA_ETARIA,
    IDENTIFICADOR_MATRIZ_FILIAL,
    IDENTIFICADOR_SOCIO,
    OPCAO_SIMPLES,
    PORTE_EMPRESA,
    SITUACAO_CADASTRAL,
    TABELAS,
    descrever,
)


def test_situacao_cadastral_tem_5_codigos_canonicos() -> None:
    assert set(SITUACAO_CADASTRAL.keys()) == {"01", "02", "03", "04", "08"}
    assert SITUACAO_CADASTRAL["02"] == "ATIVA"


def test_identificador_socio_tem_3_tipos() -> None:
    assert set(IDENTIFICADOR_SOCIO.keys()) == {"1", "2", "3"}


def test_faixa_etaria_tem_10_faixas() -> None:
    assert set(FAIXA_ETARIA.keys()) == {str(i) for i in range(10)}
    assert FAIXA_ETARIA["0"] == "Não se aplica"


def test_matriz_filial() -> None:
    assert IDENTIFICADOR_MATRIZ_FILIAL == {"1": "Matriz", "2": "Filial"}


def test_opcao_simples() -> None:
    assert set(OPCAO_SIMPLES.keys()) == {"S", "N"}


def test_porte_empresa_codigos_oficiais() -> None:
    assert set(PORTE_EMPRESA.keys()) == {"00", "01", "03", "05"}


def test_registry_tabelas_cobre_todas() -> None:
    esperado = {
        "situacao_cadastral",
        "identificador_socio",
        "faixa_etaria",
        "identificador_matriz_filial",
        "opcao_simples",
        "porte_empresa",
    }
    assert set(TABELAS.keys()) == esperado


def test_descrever_codigo_conhecido() -> None:
    assert descrever("situacao_cadastral", "02") == "ATIVA"
    assert descrever("identificador_socio", "1") == "Pessoa Jurídica"
    assert descrever("faixa_etaria", "5") == "41 a 50 anos"


def test_descrever_codigo_desconhecido_retorna_none() -> None:
    assert descrever("situacao_cadastral", "99") is None
    assert descrever("porte_empresa", "ZZ") is None


def test_descrever_tabela_desconhecida_levanta() -> None:
    with pytest.raises(KeyError):
        descrever("inexistente", "01")
