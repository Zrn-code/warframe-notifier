"""HTTP client for the warframestat.us API: shared Session, timeouts, retry/backoff."""

import logging
import random
import time

import requests

log = logging.getLogger(__name__)


class HttpError(Exception):
    pass


class HttpClient:
    def __init__(self, base_url, http_cfg, language="en", session=None):
        self.base_url = base_url.rstrip("/")
        self.cfg = http_cfg
        self.language = language
        self.session = session or requests.Session()
        self.session.headers.update(
            {"User-Agent": "warframe-notifier/1.0 (personal)", "Accept": "application/json"}
        )

    def get_json(self, endpoint, params=None):
        """GET {base}{endpoint} as JSON. Returns None on 404 (endpoint inactive).

        Retries transient failures with exponential backoff (1s, 2s, 4s ... + jitter).
        Raises HttpError after exhausting retries.
        """
        url = self.base_url + endpoint
        query = {"language": self.language}
        if params:
            query.update(params)

        last_exc = None
        for attempt in range(self.cfg.retries + 1):
            try:
                resp = self.session.get(
                    url, params=query, timeout=(self.cfg.connect_timeout, self.cfg.read_timeout)
                )
                if resp.status_code == 404:
                    return None  # e.g. arbitration can be absent
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                if attempt < self.cfg.retries:
                    delay = (2 ** attempt) + random.uniform(0, 0.5)
                    log.warning("GET %s failed (%s); retry %d in %.1fs", endpoint, exc, attempt + 1, delay)
                    time.sleep(delay)
        raise HttpError(f"GET {endpoint} failed after {self.cfg.retries} retries: {last_exc}")
