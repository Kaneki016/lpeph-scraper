"""HTTP client for the LPPEH Business Information System (bis.lpeph.gov.my)."""

from __future__ import annotations

import re
import threading
import time

import requests
import urllib3

BASE_URL = "https://bis.lpeph.gov.my"
DEFAULT_HEADERS = {
    "User-Agent": "lpeph-scraper/0.1 (python-requests)",
    "Accept": "application/json",
    "Referer": f"{BASE_URL}/search",
}

# Trailing "(...)" allowing one nested level, e.g. "3M REALTORS (E (3) 0485-2)".
_REG_NO = re.compile(r"\(((?:[^()]|\([^()]*\))*)\)\s*$")


def registration_no(label: str | None) -> str | None:
    """Extract the registration number from a search label, e.g. 'ACME (E (3) 0485)'."""
    m = _REG_NO.search(label or "")
    return m.group(1).strip() if m else None


class LpephClient:
    """Thread-safe client: one requests.Session per thread, with retries."""

    def __init__(self, base_url: str = BASE_URL, verify_tls: bool = False,
                 timeout: float = 45, retries: int = 5, backoff: float = 0.5):
        self.base_url = base_url.rstrip("/")
        self.verify_tls = verify_tls
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self._local = threading.local()
        if not verify_tls:
            # The site serves an incomplete certificate chain; verification fails on most systems.
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @property
    def session(self) -> requests.Session:
        if not hasattr(self._local, "session"):
            s = requests.Session()
            s.headers.update(DEFAULT_HEADERS)
            s.verify = self.verify_tls
            self._local.session = s
        return self._local.session

    def _post(self, path: str, payload: dict, timeout: float | None = None):
        r = self.session.post(self.base_url + path, json=payload, timeout=timeout or self.timeout)
        r.raise_for_status()
        return r.json()

    def search_firms(self) -> list[dict]:
        """Return every firm as {'code': ..., 'label': 'NAME (REG NO)'}."""
        return self._post("/api/firm/search", {}, timeout=120)

    def firm_info(self, code) -> dict | None:
        """Return full firm details, or None after exhausting retries.

        The API sometimes returns empty/partial objects under load, so a response
        only counts if it has a firm_name and status_id.
        """
        for attempt in range(self.retries):
            try:
                d = self._post("/api/firm/info", {"firm_id": code})
                if isinstance(d, dict) and d.get("firm_name") and "status_id" in d:
                    return d
            except (requests.RequestException, ValueError):
                pass
            time.sleep(self.backoff * (attempt + 1))
        return None
