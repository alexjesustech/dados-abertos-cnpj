"""Tool delta_mensal — MVP que devolve metadados de controle_importacao."""

from __future__ import annotations

from types import ModuleType


def test_delta_mensal_lista_periodo_2026_05(mcp_module: ModuleType) -> None:
    out = mcp_module.delta_mensal()
    assert "periodos" in out
    assert len(out["periodos"]) == 1
    periodo = out["periodos"][0]
    assert periodo["periodo"] == "2026-05"
    assert periodo["arquivos"] == 3
    assert periodo["ultima_data"] == "2026-05-23 04:20:00"


def test_delta_mensal_carrega_aviso_mvp(mcp_module: ModuleType) -> None:
    """Tool deixa explícito no payload que ainda é MVP."""
    out = mcp_module.delta_mensal()
    assert "aviso" in out
    assert "MVP" in out["aviso"]
