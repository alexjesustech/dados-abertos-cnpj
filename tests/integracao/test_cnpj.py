"""Rotas /api/v1/cnpj/{cnpj} — payload completo, 404, 422 e mascaramento."""

from __future__ import annotations

from fastapi.testclient import TestClient

from cnpj_lib.validador import validar

CNPJ_INVALIDO_DV = "12345678901234"  # base válida [0-9A-Z], DVs propositalmente errados


def test_get_matriz_devolve_payload_completo(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    resp = client.get(f"/api/v1/cnpj/{cnpjs['matriz_a']}")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["cnpj"]["completo"] == cnpjs["matriz_a"]
    assert body["cnpj"]["partes"]["basico"] == "11222333"
    assert body["cnpj"]["partes"]["ordem"] == "0001"
    assert body["cnpj"]["alfanumerico"] is False

    empresa = body["empresa"]
    assert empresa["razao_social"] == "ACME LTDA"
    assert empresa["natureza_juridica"]["descricao"] == "Sociedade Empresária Limitada"
    assert empresa["qualificacao_responsavel"]["descricao"] == "Sócio-Administrador"
    assert empresa["porte"]["codigo"] == "03"
    assert empresa["capital_social"] == "1000000.00"
    assert empresa["capital_social_formatado"] == "R$ 1.000.000,00"

    estab = body["estabelecimento"]
    assert estab["matriz_filial"]["codigo"] == "1"
    assert estab["situacao"]["codigo"] == "02"
    assert estab["cnae_principal"]["codigo"] == "6204000"
    assert len(estab["cnaes_secundarios"]) == 1
    assert estab["cnaes_secundarios"][0]["codigo"] == "4751201"
    assert estab["endereco"]["municipio"]["descricao"] == "PORTO VELHO"
    assert estab["contato"]["email"] == "contato@acme.test"

    assert body["estabelecimentos_filiais"]["total"] == 2
    assert body["estabelecimentos_filiais"]["tem_mais"] is True
    assert body["estabelecimentos_filiais"]["link"] == "/cnpj/11222333/estabelecimentos"

    assert body["socios"]["total"] == 5
    assert body["socios"]["retornados"] == 5  # default socios_limite=50
    assert body["socios"]["tem_mais"] is False
    assert body["socios"]["link"] is None


def test_get_filial_devolve_estabelecimento_filial(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    resp = client.get(f"/api/v1/cnpj/{cnpjs['filial_a']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["estabelecimento"]["matriz_filial"]["codigo"] == "2"
    assert body["estabelecimento"]["nome_fantasia"] == "ACME FILIAL"
    # Empresa é a mesma — totais idênticos
    assert body["empresa"]["razao_social"] == "ACME LTDA"
    assert body["estabelecimentos_filiais"]["total"] == 2


def test_get_cnpj_alfanumerico_e_sem_simples(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    resp = client.get(f"/api/v1/cnpj/{cnpjs['matriz_b']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cnpj"]["alfanumerico"] is True
    assert body["cnpj"]["partes"]["basico"] == "12ABC345"
    assert body["cnpj"]["partes"]["ordem"] == "01DE"
    assert body["empresa"]["simples"] is None
    assert body["socios"]["total"] == 0
    assert body["estabelecimentos_filiais"]["total"] == 1
    assert body["estabelecimentos_filiais"]["tem_mais"] is False


def test_get_cnpj_com_separadores_normalizados(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    """O dependency `normalizar()` retira separadores não-alfanuméricos.

    Não inclui `/` no caminho porque o roteamento HTTP trata como path
    separator; testamos pontos e hífens, suficientes para exercitar o
    fluxo de normalização.
    """
    completo = cnpjs["matriz_a"]
    com_sep = f"{completo[0:2]}.{completo[2:5]}.{completo[5:8]}-{completo[8:12]}-{completo[12:14]}"
    resp = client.get(f"/api/v1/cnpj/{com_sep}")
    assert resp.status_code == 200
    assert resp.json()["cnpj"]["completo"] == completo


def test_socios_limite_trunca_inline_e_emite_link(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    resp = client.get(f"/api/v1/cnpj/{cnpjs['matriz_a']}?socios_limite=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["socios"]["total"] == 5
    assert body["socios"]["retornados"] == 2
    assert body["socios"]["tem_mais"] is True
    assert body["socios"]["link"] == "/cnpj/11222333/socios"
    assert len(body["socios"]["lista"]) == 2


def test_socios_limite_zero_rejeitado_422(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    resp = client.get(f"/api/v1/cnpj/{cnpjs['matriz_a']}?socios_limite=0")
    assert resp.status_code == 422


def test_cnpj_valido_mas_inexistente_devolve_404(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    cnpj = cnpjs["inexistente"]
    assert validar(cnpj)  # garante que não é 422
    resp = client.get(f"/api/v1/cnpj/{cnpj}")
    assert resp.status_code == 404


def test_cnpj_invalido_devolve_422(client: TestClient) -> None:
    assert not validar(CNPJ_INVALIDO_DV)
    resp = client.get(f"/api/v1/cnpj/{CNPJ_INVALIDO_DV}")
    assert resp.status_code == 422


def test_cnpj_curto_devolve_422(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/abc")
    assert resp.status_code == 422


def test_socio_pf_documento_mascarado(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    body = client.get(f"/api/v1/cnpj/{cnpjs['matriz_a']}").json()
    pf = next(s for s in body["socios"]["lista"] if s["identificador"]["codigo"] == "2")
    assert pf["documento"]["tipo"] == "cpf"
    assert pf["documento"]["mascarado"] is True
    assert pf["documento"]["valor"].startswith("***")


def test_socio_pj_documento_nao_mascarado(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    body = client.get(f"/api/v1/cnpj/{cnpjs['matriz_a']}").json()
    pj = next(s for s in body["socios"]["lista"] if s["identificador"]["codigo"] == "1")
    assert pj["documento"]["tipo"] == "cnpj"
    assert pj["documento"]["mascarado"] is False
    assert pj["documento"]["valor"] == "99888777000166"


def test_socio_estrangeiro_tem_representante_legal(
    client: TestClient,
    cnpjs: dict[str, str],
) -> None:
    body = client.get(f"/api/v1/cnpj/{cnpjs['matriz_a']}").json()
    estrangeiro = next(s for s in body["socios"]["lista"] if s["identificador"]["codigo"] == "3")
    rep = estrangeiro["representante_legal"]
    assert rep is not None
    assert rep["nome"] == "JOSE REPRESENTANTE"
    assert rep["qualificacao"]["descricao"] == "Sócio-Administrador"
    assert rep["documento"]["mascarado"] is True
