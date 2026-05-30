"""Tools utilitárias: validar_cnpj + descrever_codigo."""

from __future__ import annotations

from types import ModuleType


def test_validar_cnpj_numerico_aceito(mcp_module: ModuleType, cnpjs: dict[str, str]) -> None:
    out = mcp_module.validar_cnpj(cnpjs["matriz_a"])
    assert out == {"cnpj": cnpjs["matriz_a"], "valido": True, "alfanumerico": False}


def test_validar_cnpj_alfanumerico_aceito(mcp_module: ModuleType, cnpjs: dict[str, str]) -> None:
    out = mcp_module.validar_cnpj(cnpjs["matriz_b"])
    assert out == {"cnpj": cnpjs["matriz_b"], "valido": True, "alfanumerico": True}


def test_validar_cnpj_invalido_marca_falso(mcp_module: ModuleType) -> None:
    out = mcp_module.validar_cnpj("12345678901234")
    assert out["valido"] is False
    assert out["alfanumerico"] is False  # não computa pra inválido


def test_validar_cnpj_aceita_mascara(mcp_module: ModuleType, cnpjs: dict[str, str]) -> None:
    completo = cnpjs["matriz_a"]
    com_mascara = (
        f"{completo[0:2]}.{completo[2:5]}.{completo[5:8]}/{completo[8:12]}-{completo[12:14]}"
    )
    out = mcp_module.validar_cnpj(com_mascara)
    assert out["valido"] is True


def test_descrever_codigo_lookup_cnaes(mcp_module: ModuleType) -> None:
    out = mcp_module.descrever_codigo(tabela="cnaes", codigo="6204000")
    assert out == {
        "tabela": "cnaes",
        "codigo": "6204000",
        "descricao": "Consultoria em tecnologia da informação",
    }


def test_descrever_codigo_lookup_municipios(mcp_module: ModuleType) -> None:
    out = mcp_module.descrever_codigo(tabela="municipios", codigo="7107")
    assert out["descricao"] == "PORTO VELHO"


def test_descrever_codigo_dominio_situacao_cadastral(mcp_module: ModuleType) -> None:
    """`situacao_cadastral` é tabela hardcoded em cnpj_lib.dominio, não lookup."""
    out = mcp_module.descrever_codigo(tabela="situacao_cadastral", codigo="02")
    assert out["tabela"] == "situacao_cadastral"
    assert out["codigo"] == "02"
    assert out["descricao"] == "ATIVA"


def test_descrever_codigo_dominio_identificador_socio(mcp_module: ModuleType) -> None:
    out = mcp_module.descrever_codigo(tabela="identificador_socio", codigo="1")
    assert out["descricao"] is not None


def test_descrever_codigo_inexistente_devolve_descricao_none(mcp_module: ModuleType) -> None:
    out = mcp_module.descrever_codigo(tabela="cnaes", codigo="9999999")
    assert out["codigo"] == "9999999"
    assert out["descricao"] is None
