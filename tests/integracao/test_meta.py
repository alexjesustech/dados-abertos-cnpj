"""Rotas /api/v1/health, /periodo-atual e /stats contra o SQLite descartável."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_health_returns_ok_com_timestamp_utc(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["timestamp"].endswith("Z")


def test_periodo_atual_derivado_da_controle_importacao(client: TestClient) -> None:
    resp = client.get("/api/v1/periodo-atual")
    assert resp.status_code == 200
    assert resp.json() == {"periodo": "2026-05"}


def test_stats_conta_as_quatro_tabelas_fato(
    client: TestClient,
    tmp_db_path: Path,
) -> None:
    resp = client.get("/api/v1/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["empresas"] == 2
    assert body["estabelecimentos"] == 3
    assert body["socios"] == 5
    assert body["simples"] == 1
    assert body["db_path"] == str(tmp_db_path)


def test_stats_segundo_hit_devolve_mesmo_corpo(client: TestClient) -> None:
    """Sanidade: cache lazy não corrompe a resposta entre requests."""
    primeira = client.get("/api/v1/stats").json()
    segunda = client.get("/api/v1/stats").json()
    assert primeira == segunda
