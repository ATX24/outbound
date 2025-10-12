from __future__ import annotations

from typing import Any, Dict
import requests
from ..config import load_settings


class FirecrawlClient:
    def __init__(self, api_key: str, timeout_seconds: int = 30) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        self.timeout_seconds = timeout_seconds
        self.base_url = "https://api.firecrawl.dev/v0"

    def crawl(self, url: str, **options: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"url": url}
        payload.update(options)
        resp = self.session.post(f"{self.base_url}/crawl", json=payload, timeout=self.timeout_seconds)
        resp.raise_for_status()
        return resp.json()

    def scrape(self, url: str, **options: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"url": url}
        payload.update(options)
        resp = self.session.post(f"{self.base_url}/scrape", json=payload, timeout=self.timeout_seconds)
        resp.raise_for_status()
        return resp.json()


_firecrawl_client: FirecrawlClient | None = None


def get_firecrawl() -> FirecrawlClient:
    global _firecrawl_client
    if _firecrawl_client is None:
        settings = load_settings()
        if not settings.firecrawl_api_key:
            raise RuntimeError("FIRECRAWL_API_KEY is required")
        _firecrawl_client = FirecrawlClient(
            api_key=settings.firecrawl_api_key,
            timeout_seconds=settings.requests_timeout_seconds,
        )
    return _firecrawl_client
