"""Testes de cnpj_lib.validador — algoritmo módulo 11 (alfa + num)."""
from __future__ import annotations

from string import ascii_uppercase, digits

import pytest
from hypothesis import given, strategies as st

from cnpj_lib.validador import (
    calcular_dv,
    eh_alfanumerico,
    validar,
)

# Casos oficiais — NT Conjunta 2025.001 / FAQ RFB / cálculo passo-a-passo (Serpro/coboldicas)
CASOS_VALIDOS_ALFA = [
    "12.ABC.345/01DE-35",
    "AB12CD34/EFGH-83",
]

# CNPJs antigos famosos — todos retiráveis de uma busca no próprio dataset RFB
CASOS_VALIDOS_NUM = [
    "00.000.000/0001-91",   # Banco do Brasil
    "33.000.167/0001-01",   # Petrobras
    "60.701.190/0001-04",   # Itaú Unibanco
    "47.960.950/0001-21",   # Magazine Luiza
    "76.535.764/0001-43",   # Copel
    "61.198.164/0001-60",   # SBT
]

CASOS_INVALIDOS = [
    "",
    "xyz",
    "00.000.000/0001-92",       # DV1 errado
    "00.000.000/0001-90",       # DV2 errado
    "12.ABC.345/01DE-36",       # DV alfa errado
    "1234567890123",            # 13 chars
    "123456789012345",          # 15 chars
    "AAAA-BBBB-CCCC",           # estrutura errada
    "00.000.000/0001-9A",       # DV não-numérico
    "00.000.000/0001-9*",       # caractere inválido em DV
]


@pytest.mark.parametrize("cnpj", CASOS_VALIDOS_ALFA + CASOS_VALIDOS_NUM)
def test_validar_aceita_casos_oficiais(cnpj: str) -> None:
    assert validar(cnpj) is True


@pytest.mark.parametrize("cnpj", CASOS_INVALIDOS)
def test_validar_rejeita_casos_invalidos(cnpj: str) -> None:
    assert validar(cnpj) is False


def test_validar_aceita_input_none_como_invalido() -> None:
    assert validar(None) is False  # type: ignore[arg-type]


def test_validar_ignora_caixa_e_mascara() -> None:
    assert validar("00000000000191")
    assert validar("00.000.000/0001-91")
    assert validar("12.abc.345/01de-35") is True
    assert validar(" 00 000 000 0001 91 ") is True


def test_calcular_dv_caso_oficial_alfa() -> None:
    assert calcular_dv("12ABC34501DE") == "35"


def test_calcular_dv_caso_oficial_numerico() -> None:
    assert calcular_dv("000000000001") == "91"  # Banco do Brasil


def test_calcular_dv_base_invalida_levanta() -> None:
    with pytest.raises(ValueError):
        calcular_dv("ABC")
    with pytest.raises(ValueError):
        calcular_dv("12ABC34501D*")  # caractere fora [0-9A-Z]


def test_eh_alfanumerico_detecta_letras_na_base() -> None:
    assert eh_alfanumerico("12.ABC.345/01DE-35") is True
    assert eh_alfanumerico("12ABC34501DE35") is True
    assert eh_alfanumerico("00.000.000/0001-91") is False
    assert eh_alfanumerico("") is False


# --- Property test: round-trip do gerador de DV ----------------------------
_CHARSET_BASE = digits + ascii_uppercase


@given(st.text(alphabet=_CHARSET_BASE, min_size=12, max_size=12))
def test_round_trip_calcular_dv_implica_validar(base: str) -> None:
    """Pra qualquer base alfanumérica, base + DV calculado deve validar."""
    cnpj = base + calcular_dv(base)
    assert validar(cnpj) is True
