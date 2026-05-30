"""Rotas de meta-informação: health, período atual, contagens."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app.dependencias import ConnDep, SettingsDep

router = APIRouter(tags=["meta"])

_TABELAS_FATO = ("empresas", "estabelecimentos", "socios", "simples")


@router.get("/health", summary="Sonda de saúde")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


@router.get(
    "/periodo-atual",
    summary="YYYY-MM da última safra ingerida (derivado de data_importacao)",
)
def periodo_atual(conn: ConnDep) -> dict[str, str | None]:
    """Deriva o período do MAX(data_importacao) na controle_importacao.

    A tabela não armazena o período YYYY-MM da RFB explicitamente — só a
    data em que foi importada. Como o pipeline roda logo após a publicação
    mensal, a heurística é boa o bastante para esta API local. Para precisão
    absoluta, setar a env var ``CNPJ_PERIOD`` e usar ``app.state``.
    """
    cur = conn.execute(
        "SELECT SUBSTR(MAX(data_importacao), 1, 7) AS periodo FROM controle_importacao"
    )
    row = cur.fetchone()
    return {"periodo": row["periodo"] if row else None}


@router.get(
    "/stats",
    summary="Contagens por tabela (cache lazy — primeiro hit roda COUNT real)",
)
def stats(
    request: Request,
    conn: ConnDep,
    settings: SettingsDep,
) -> dict[str, int | str]:
    """Devolve contagens das 4 tabelas-fato.

    Primeiro hit roda ``COUNT(*)`` (~60s sem ANALYZE) e cacheia em ``app.state``.
    Hits subsequentes são instantâneos. Para invalidar, reiniciar a API.
    """
    cache = getattr(request.app.state, "stats_cache", None)
    if cache is None:
        cache = {}
        for nome in _TABELAS_FATO:
            cur = conn.execute(f"SELECT COUNT(*) AS c FROM {nome}")  # noqa: S608 — whitelist
            cache[nome] = int(cur.fetchone()["c"])
        request.app.state.stats_cache = cache
    return {**cache, "db_path": str(settings.db_path)}
