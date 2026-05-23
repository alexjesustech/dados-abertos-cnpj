"""Fixture específica da integração HTTP: TestClient apontando pro tmp_db.

Reusa `tmp_db_path` definido em `tests/conftest.py`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client(tmp_db_path: Path):
    """TestClient apontando pro DB descartável (DB_PATH via env)."""
    os.environ["DB_PATH"] = str(tmp_db_path)
    for mod in [m for m in list(sys.modules) if m == "app" or m.startswith("app.")]:
        sys.modules.pop(mod, None)
    from app.main import app as fastapi_app

    with TestClient(fastapi_app) as c:
        yield c
