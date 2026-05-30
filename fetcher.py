"""Fetcher dos Dados Abertos do CNPJ via WebDAV público do Nextcloud da RFB."""

import logging
import os
import re
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

WEBDAV_BASE = "https://arquivos.receitafederal.gov.br/public.php/webdav"
CNPJ_PATH = "Dados/Cadastros/CNPJ"
DEFAULT_SHARE_TOKEN = "gn672Ad4CF8N6TK"

_NS = {"d": "DAV:"}
_PERIOD_RE = re.compile(r"/(\d{4}-\d{2})/$")


class CNPJFetcher:
    def __init__(
        self,
        dir_temp,
        notifier,
        share_token: str | None = None,
        chunk_size: int = 1024 * 1024,
        max_retries: int = 5,
    ):
        self.dir_temp = Path(dir_temp)
        self.dir_temp.mkdir(parents=True, exist_ok=True)
        self.notifier = notifier
        self.chunk_size = chunk_size
        self.max_retries = max_retries

        token = share_token or os.getenv("RFB_SHARE_TOKEN") or DEFAULT_SHARE_TOKEN
        self.session = requests.Session()
        self.session.auth = (token, "")
        self.session.headers["User-Agent"] = "dados-abertos-cnpj/1.0"

    def _propfind(self, path: str) -> list[dict]:
        url = f"{WEBDAV_BASE}/{path.strip('/')}/"
        r = self.session.request("PROPFIND", url, headers={"Depth": "1"}, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        entries = []
        for resp in root.findall("d:response", _NS):
            href = resp.findtext("d:href", default="", namespaces=_NS)
            length_el = resp.find(".//d:getcontentlength", _NS)
            size = int(length_el.text) if length_el is not None and length_el.text else None
            entries.append({"href": href, "size": size})
        return entries

    def latest_period(self) -> str:
        periods = []
        for entry in self._propfind(CNPJ_PATH):
            m = _PERIOD_RE.search(entry["href"])
            if m:
                periods.append(m.group(1))
        if not periods:
            raise RuntimeError(f"Nenhum período YYYY-MM em /{CNPJ_PATH}/")
        return max(periods)

    def list_zips(self, period: str) -> list[dict]:
        zips = []
        for entry in self._propfind(f"{CNPJ_PATH}/{period}"):
            name = entry["href"].rsplit("/", 1)[-1]
            if name.lower().endswith(".zip"):
                zips.append({"name": name, "size": entry["size"]})
        return zips

    def download_zip(self, period: str, name: str, expected_size: int | None = None) -> Path:
        url = f"{WEBDAV_BASE}/{CNPJ_PATH}/{period}/{name}"
        target = self.dir_temp / name

        if expected_size is None:
            head = self.session.head(url, timeout=30)
            head.raise_for_status()
            expected_size = int(head.headers.get("Content-Length", "0"))

        if target.exists() and target.stat().st_size == expected_size:
            self.notifier.log_and_notify(f"[skip] {name} já presente ({expected_size} bytes).")
            return target

        for attempt in range(1, self.max_retries + 1):
            already = target.stat().st_size if target.exists() else 0
            if already >= expected_size:
                already = 0
            headers = {}
            mode = "wb"
            if already > 0:
                headers["Range"] = f"bytes={already}-"
                mode = "ab"
                self.notifier.log_and_notify(
                    f"[resume] {name} de {already}/{expected_size} bytes (tentativa {attempt})."
                )
            else:
                self.notifier.log_and_notify(
                    f"[get] {name} ({expected_size} bytes, tentativa {attempt})."
                )

            try:
                with self.session.get(url, headers=headers, stream=True, timeout=(15, 120)) as r:
                    if r.status_code not in (200, 206):
                        r.raise_for_status()
                    with open(target, mode) as f:
                        for chunk in r.iter_content(chunk_size=self.chunk_size):
                            if chunk:
                                f.write(chunk)
                actual = target.stat().st_size
                if actual == expected_size:
                    return target
                self.notifier.log_and_notify(
                    f"[warn] {name}: tamanho final {actual} != esperado {expected_size}.",
                    level=logging.WARNING,
                )
            except (requests.RequestException, OSError) as e:
                self.notifier.log_and_notify(
                    f"[err] {name} tentativa {attempt}/{self.max_retries}: {e}",
                    level=logging.WARNING,
                )
                time.sleep(min(2**attempt, 30))

        raise RuntimeError(f"Falha ao baixar {name} após {self.max_retries} tentativas.")

    def fetch_all(self, period: str | None = None) -> tuple[str, list[Path]]:
        if not period:
            period = self.latest_period()
        self.notifier.log_and_notify(f"Período-alvo: {period}")

        zips = self.list_zips(period)
        total = sum(z["size"] or 0 for z in zips)
        self.notifier.log_and_notify(
            f"{len(zips)} arquivos ZIP no período {period} (~{total / 1024**3:.2f} GB)."
        )

        downloaded = []
        for z in zips:
            downloaded.append(self.download_zip(period, z["name"], z["size"]))
        return period, downloaded
