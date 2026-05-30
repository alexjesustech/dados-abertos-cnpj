"""Testes de cnpj_lib.formatador — normalização, máscara, parsing."""

from __future__ import annotations

import pytest

from cnpj_lib.formatador import (
    formatar,
    fragmentar,
    mascarar_cpf,
    normalizar,
    parsear_data_yyyymmdd,
)

# --- normalizar -----------------------------------------------------------


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("00.000.000/0001-91", "00000000000191"),
        ("12.ABC.345/01DE-35", "12ABC34501DE35"),
        ("12.abc.345/01de-35", "12ABC34501DE35"),
        ("  00 000 000 0001 91 ", "00000000000191"),
        ("", ""),
    ],
)
def test_normalizar(entrada: str, esperado: str) -> None:
    assert normalizar(entrada) == esperado


# --- formatar -------------------------------------------------------------


def test_formatar_aplica_mascara_padrao() -> None:
    assert formatar("00000000000191") == "00.000.000/0001-91"


def test_formatar_aceita_alfa_minusculo() -> None:
    assert formatar("12abc34501de35") == "12.ABC.345/01DE-35"


def test_formatar_aceita_entrada_ja_mascarada() -> None:
    assert formatar("00.000.000/0001-91") == "00.000.000/0001-91"


def test_formatar_recusa_tamanho_errado() -> None:
    with pytest.raises(ValueError):
        formatar("1234")
    with pytest.raises(ValueError):
        formatar("000000000001911")  # 15 chars


# --- fragmentar -----------------------------------------------------------


def test_fragmentar_devolve_basico_ordem_dv() -> None:
    assert fragmentar("00.000.000/0001-91") == ("00000000", "0001", "91")
    assert fragmentar("12ABC34501DE35") == ("12ABC345", "01DE", "35")


def test_fragmentar_recusa_tamanho_errado() -> None:
    with pytest.raises(ValueError):
        fragmentar("123")


# --- mascarar_cpf ---------------------------------------------------------


def test_mascarar_cpf_padrao_rfb() -> None:
    assert mascarar_cpf("12345678901") == "***456789**"


def test_mascarar_cpf_ignora_pontuacao() -> None:
    assert mascarar_cpf("123.456.789-01") == "***456789**"


def test_mascarar_cpf_recusa_tamanho_errado() -> None:
    with pytest.raises(ValueError):
        mascarar_cpf("123")


# --- parsear_data_yyyymmdd ------------------------------------------------


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("19690801", "1969-08-01"),
        ("20260706", "2026-07-06"),
    ],
)
def test_parsear_data_valida(entrada: str, esperado: str) -> None:
    assert parsear_data_yyyymmdd(entrada) == esperado


@pytest.mark.parametrize(
    "entrada",
    ["00000000", "", None, "ABCDEFGH", "2025130A", "20251301", "20250230", "1234"],
)
def test_parsear_data_invalida_retorna_none(entrada: str | None) -> None:
    assert parsear_data_yyyymmdd(entrada) is None


# --- round-trip -----------------------------------------------------------


def test_normalizar_formatar_roundtrip() -> None:
    """normalizar(formatar(s)) == normalizar(s) para qualquer CNPJ válido."""
    for s in ("00.000.000/0001-91", "12ABC34501DE35", "AB12CD340001DE35"[:14]):
        assert normalizar(formatar(s)) == normalizar(s)
