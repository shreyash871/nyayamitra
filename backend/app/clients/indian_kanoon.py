import time

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings


class RateLimiter:
    """Ensures we don't fire requests faster than allowed.
    Waits between calls so we stay polite to the API."""

    def __init__(self, min_interval_seconds: float = 1.0):
        self.min_interval = min_interval_seconds
        self._last_call = 0.0

    def wait(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.time()


class IndianKanoonClient:
    """Talks to the Indian Kanoon API. The rest of the app never
    touches HTTP directly — it just calls these methods."""

    def __init__(self):
        self.base_url = settings.INDIAN_KANOON_BASE_URL
        self.token = settings.INDIAN_KANOON_API_TOKEN
        self.limiter = RateLimiter(min_interval_seconds=1.0)

    def _headers(self) -> dict:
        # Indian Kanoon expects: Authorization: Token <your_token>
        return {
            "Authorization": f"Token {self.token}",
            "Accept": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def search(self, query: str, page: int = 0) -> dict:
        """Search judgments. NOTE: page starts at 0, not 1."""
        self.limiter.wait()
        # Indian Kanoon uses POST for search, with formInput as the query
        resp = requests.post(
            f"{self.base_url}/search/",
            headers=self._headers(),
            data={"formInput": query, "pagenum": page},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def get_document(self, doc_id: str) -> dict:
        """Fetch the full text of one judgment by its document id."""
        self.limiter.wait()
        resp = requests.post(
            f"{self.base_url}/doc/{doc_id}/",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
