"""Fixture específica do MCP: módulo `mcp_server.server` apontando pro tmp_db.

Reusa `tmp_db_path` definido em `tests/conftest.py`. As tools FastMCP são
funções Python normais (o decorator `@mcp.tool()` só registra no servidor;
não envolve em wrapper), então os testes chamam diretamente em vez de
subir um cliente MCP por stdio.

Cada tool abre/fecha sua própria conexão SQLite via `get_settings()`, que
relê a env a cada call — basta `DB_PATH` estar setado quando a tool roda.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture(scope="session")
def mcp_module(tmp_db_path: Path) -> ModuleType:
    """Importa mcp_server.server contra o tmp_db e devolve o módulo.

    Limpa caches eventuais de `mcp_server.*` e do `_lookups_cache` global
    para que o primeiro `_lookups()` (lazy) leia da fixture.
    """
    os.environ["DB_PATH"] = str(tmp_db_path)
    for mod in [m for m in list(sys.modules) if m == "mcp_server" or m.startswith("mcp_server.")]:
        sys.modules.pop(mod, None)
    import mcp_server.server as server  # noqa: PLC0415 — import tardio proposital

    server._lookups_cache = None
    server._periodo_cache = None
    return server
