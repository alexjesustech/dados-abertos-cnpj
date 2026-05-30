"""Tools de consulta por CNPJ: buscar_empresa + listar_socios + listar_filiais."""

from __future__ import annotations

from types import ModuleType

import pytest

# ---------- buscar_empresa ----------


def test_buscar_empresa_devolve_dict_serializavel(
    mcp_module: ModuleType,
    cnpjs: dict[str, str],
) -> None:
    """`buscar_empresa` reusa o serviço da API e devolve dict pra JSON."""
    out = mcp_module.buscar_empresa(cnpj=cnpjs["matriz_a"])
    assert out["cnpj"]["completo"] == cnpjs["matriz_a"]
    assert out["empresa"]["razao_social"] == "ACME LTDA"
    assert out["empresa"]["capital_social_formatado"] == "R$ 1.000.000,00"
    assert out["estabelecimento"]["matriz_filial"]["codigo"] == "1"
    assert out["socios"]["total"] == 5
    assert out["socios"]["retornados"] == 5  # default socios_limite=20, mas só temos 5


def test_buscar_empresa_socios_limite_trunca(
    mcp_module: ModuleType,
    cnpjs: dict[str, str],
) -> None:
    out = mcp_module.buscar_empresa(cnpj=cnpjs["matriz_a"], socios_limite=2)
    assert out["socios"]["total"] == 5
    assert out["socios"]["retornados"] == 2
    assert out["socios"]["tem_mais"] is True
    assert out["socios"]["link"] == "/cnpj/11222333/socios"


def test_buscar_empresa_alfanumerica(
    mcp_module: ModuleType,
    cnpjs: dict[str, str],
) -> None:
    out = mcp_module.buscar_empresa(cnpj=cnpjs["matriz_b"])
    assert out["cnpj"]["alfanumerico"] is True
    assert out["empresa"]["simples"] is None
    assert out["socios"]["total"] == 0


def test_buscar_empresa_cnpj_invalido_levanta_value_error(mcp_module: ModuleType) -> None:
    with pytest.raises(ValueError, match="CNPJ inválido"):
        mcp_module.buscar_empresa(cnpj="12345678901234")


def test_buscar_empresa_cnpj_inexistente_levanta_value_error(
    mcp_module: ModuleType,
    cnpjs: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match="não encontrado"):
        mcp_module.buscar_empresa(cnpj=cnpjs["inexistente"])


# ---------- listar_socios ----------


def test_listar_socios_pagina_inicial(mcp_module: ModuleType) -> None:
    out = mcp_module.listar_socios(cnpj_basico="11222333", limit=2, offset=0)
    assert out["pagina"] == {"total": 5, "retornados": 2, "tem_mais": True}
    assert len(out["socios"]) == 2


def test_listar_socios_ultima_pagina_sem_tem_mais(mcp_module: ModuleType) -> None:
    out = mcp_module.listar_socios(cnpj_basico="11222333", limit=2, offset=4)
    assert out["pagina"] == {"total": 5, "retornados": 1, "tem_mais": False}


def test_listar_socios_basico_alfa_vazio(mcp_module: ModuleType) -> None:
    out = mcp_module.listar_socios(cnpj_basico="12ABC345")
    assert out["pagina"]["total"] == 0
    assert out["socios"] == []


def test_listar_socios_basico_invalido_levanta(mcp_module: ModuleType) -> None:
    with pytest.raises(ValueError, match="8 chars"):
        mcp_module.listar_socios(cnpj_basico="abc")


def test_listar_socios_aceita_mascara_no_basico(mcp_module: ModuleType) -> None:
    """normalizar() retira separadores antes do check de tamanho."""
    out = mcp_module.listar_socios(cnpj_basico="11.222.333")
    assert out["pagina"]["total"] == 5


# ---------- listar_filiais ----------


def test_listar_filiais_total_corresponde(mcp_module: ModuleType) -> None:
    out = mcp_module.listar_filiais(cnpj_basico="11222333", limit=10)
    assert out["pagina"]["total"] == 2
    assert out["pagina"]["retornados"] == 2
    assert out["pagina"]["tem_mais"] is False


def test_listar_filiais_paginada(mcp_module: ModuleType) -> None:
    out = mcp_module.listar_filiais(cnpj_basico="11222333", limit=1, offset=0)
    assert out["pagina"] == {"total": 2, "retornados": 1, "tem_mais": True}


def test_listar_filiais_basico_alfa(mcp_module: ModuleType) -> None:
    out = mcp_module.listar_filiais(cnpj_basico="12ABC345")
    assert out["pagina"]["total"] == 1
