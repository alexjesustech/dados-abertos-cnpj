"""Subrotas paginadas /cnpj/{basico}/socios e /cnpj/{basico}/estabelecimentos."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_socios_primeira_pagina_indica_tem_mais(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/11222333/socios?limit=2&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["retornados"] == 2
    assert body["tem_mais"] is True
    assert len(body["lista"]) == 2


def test_socios_ultima_pagina_sem_tem_mais(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/11222333/socios?limit=2&offset=4")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["retornados"] == 1
    assert body["tem_mais"] is False
    assert len(body["lista"]) == 1


def test_socios_offset_alem_do_total_retorna_vazio(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/11222333/socios?limit=10&offset=999")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["retornados"] == 0
    assert body["tem_mais"] is False
    assert body["lista"] == []


def test_estabelecimentos_paginados_com_tem_mais(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/11222333/estabelecimentos?limit=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["retornados"] == 1
    assert body["tem_mais"] is True


def test_estabelecimentos_sem_paginacao_quando_total_eh_unico(client: TestClient) -> None:
    """Empresa B tem só 1 estabelecimento — limit alto não deve marcar tem_mais."""
    resp = client.get("/api/v1/cnpj/12ABC345/estabelecimentos?limit=50")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["retornados"] == 1
    assert body["tem_mais"] is False


def test_limit_zero_rejeitado_422(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/11222333/socios?limit=0")
    assert resp.status_code == 422


def test_limit_acima_do_max_rejeitado_422(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/11222333/socios?limit=999")
    assert resp.status_code == 422


def test_offset_negativo_rejeitado_422(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/11222333/socios?limit=10&offset=-1")
    assert resp.status_code == 422


def test_basico_curto_rejeitado_422(client: TestClient) -> None:
    resp = client.get("/api/v1/cnpj/abc/socios")
    assert resp.status_code == 422


def test_basico_alfanumerico_aceito(client: TestClient) -> None:
    """A base 12ABC345 da empresa B deve passar pelo validator BasicoValidado."""
    resp = client.get("/api/v1/cnpj/12ABC345/socios")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["retornados"] == 0
    assert body["tem_mais"] is False


def test_basico_aceita_mascara(client: TestClient) -> None:
    """normalizar() retira separadores antes do check de 8 chars [0-9A-Z]."""
    resp = client.get("/api/v1/cnpj/11.222.333/socios")
    assert resp.status_code == 200
    assert resp.json()["total"] == 5
