"""Tools de busca cruzada: vinculos_pj + cnaes_por_municipio + empresas_por_cnae.

Cenário esperado no banco descartável (ver tests/conftest.py):

  município 7107 (PORTO VELHO):
    - matriz A   cnae 6204000  UF=RO
    - filial A   cnae 4751201  UF=RO
    - matriz B   cnae 6204000  UF=SP

  Total por CNAE em 7107:  6204000 → 2 estabs · 4751201 → 1 estab
  Total por CNAE 6204000:  2 estabs (matriz A em RO + matriz B em SP)
"""
from __future__ import annotations

from types import ModuleType

# ---------- vinculos_pj ----------

def test_vinculos_pj_para_holding_pj(mcp_module: ModuleType) -> None:
    """O CNPJ da holding aparece como sócio (ident=1) da empresa A."""
    out = mcp_module.vinculos_pj(documento="99888777000166")
    assert out["pagina"]["total"] == 1
    assert len(out["vinculos"]) == 1
    vinculo = out["vinculos"][0]
    assert vinculo["cnpj_basico"] == "11222333"
    assert vinculo["identificador"]["codigo"] == "1"
    assert vinculo["documento"] == "99888777000166"
    assert vinculo["qualificacao"]["descricao"] == "Sócio"


def test_vinculos_pj_para_pf_mascarada(mcp_module: ModuleType) -> None:
    """CPF mascarado padrão RFB também é chave de busca."""
    out = mcp_module.vinculos_pj(documento="***123456**")
    assert out["pagina"]["total"] == 1
    assert out["vinculos"][0]["nome_razao_social"] == "JOAO DA SILVA"
    assert out["vinculos"][0]["identificador"]["codigo"] == "2"


def test_vinculos_pj_documento_inexistente(mcp_module: ModuleType) -> None:
    out = mcp_module.vinculos_pj(documento="00000000000000")
    assert out["pagina"]["total"] == 0
    assert out["vinculos"] == []


def test_vinculos_pj_paginada(mcp_module: ModuleType) -> None:
    out = mcp_module.vinculos_pj(documento="99888777000166", limit=1, offset=0)
    assert out["pagina"]["retornados"] == 1
    assert out["pagina"]["tem_mais"] is False


# ---------- cnaes_por_municipio ----------

def test_cnaes_por_municipio_porto_velho(mcp_module: ModuleType) -> None:
    out = mcp_module.cnaes_por_municipio(municipio_codigo="7107")
    assert out["municipio"] == "PORTO VELHO"
    assert out["pagina"]["total"] == 2  # 2 CNAEs distintos
    cnaes = {item["cnae"]["codigo"]: item["total_estabelecimentos"] for item in out["cnaes"]}
    assert cnaes == {"6204000": 2, "4751201": 1}


def test_cnaes_por_municipio_inexistente(mcp_module: ModuleType) -> None:
    out = mcp_module.cnaes_por_municipio(municipio_codigo="0000")
    assert out["pagina"]["total"] == 0
    assert out["cnaes"] == []


def test_cnaes_por_municipio_paginada(mcp_module: ModuleType) -> None:
    out = mcp_module.cnaes_por_municipio(municipio_codigo="7107", limit=1, offset=0)
    assert out["pagina"]["retornados"] == 1
    assert out["pagina"]["tem_mais"] is True


# ---------- empresas_por_cnae ----------

def test_empresas_por_cnae_sem_filtro(mcp_module: ModuleType) -> None:
    out = mcp_module.empresas_por_cnae(cnae="6204000")
    assert out["cnae"] == {
        "codigo": "6204000",
        "descricao": "Consultoria em tecnologia da informação",
    }
    assert out["pagina"]["total"] == 2
    razoes = {emp["razao_social"] for emp in out["empresas"]}
    assert razoes == {"ACME LTDA", "ALFANUM TECH"}


def test_empresas_por_cnae_filtrado_por_uf_ro(mcp_module: ModuleType) -> None:
    out = mcp_module.empresas_por_cnae(cnae="6204000", uf="RO")
    assert out["pagina"]["total"] == 1
    assert out["empresas"][0]["cnpj_basico"] == "11222333"
    assert out["empresas"][0]["uf"] == "RO"


def test_empresas_por_cnae_filtrado_por_uf_sp(mcp_module: ModuleType) -> None:
    out = mcp_module.empresas_por_cnae(cnae="6204000", uf="SP")
    assert out["pagina"]["total"] == 1
    assert out["empresas"][0]["cnpj_basico"] == "12ABC345"


def test_empresas_por_cnae_filtrado_por_municipio(mcp_module: ModuleType) -> None:
    out = mcp_module.empresas_por_cnae(cnae="6204000", municipio_codigo="7107")
    assert out["pagina"]["total"] == 2


def test_empresas_por_cnae_combinando_municipio_e_uf(mcp_module: ModuleType) -> None:
    out = mcp_module.empresas_por_cnae(cnae="6204000", municipio_codigo="7107", uf="RO")
    assert out["pagina"]["total"] == 1


def test_empresas_por_cnae_inexistente(mcp_module: ModuleType) -> None:
    out = mcp_module.empresas_por_cnae(cnae="9999999")
    assert out["pagina"]["total"] == 0
    assert out["empresas"] == []
