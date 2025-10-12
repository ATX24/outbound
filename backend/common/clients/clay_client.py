from __future__ import annotations

from typing import Any, Dict
import requests
from ..config import load_settings


class ClayClient:
    def __init__(self, webhook_url: str, api_key: str | None, timeout_seconds: int = 30) -> None:
        self.webhook_url = webhook_url
        self.session = requests.Session()
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self.session.headers.update(headers)
        self.timeout_seconds = timeout_seconds

    def ingest_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        resp = self.session.post(self.webhook_url, json={"records": records}, timeout=self.timeout_seconds)
        resp.raise_for_status()
        return resp.json() if resp.content else {}


def get_clay_for_pipeline(pipeline: str) -> ClayClient:
    settings = load_settings()
    webhook_map = {
        "bigtech": settings.clay_webhook_url_bigtech or settings.clay_webhook_url,
        "vc": settings.clay_webhook_url_vc or settings.clay_webhook_url,
        "ut": settings.clay_webhook_url_ut or settings.clay_webhook_url,
    }
    webhook_url = webhook_map.get(pipeline)
    if not webhook_url:
        raise RuntimeError(
            "Missing Clay webhook URL for pipeline. Set CLAY_WEBHOOK_URL_<PIPE> or CLAY_WEBHOOK_URL."
        )
    return ClayClient(webhook_url=webhook_url, api_key=settings.clay_api_key, timeout_seconds=settings.requests_timeout_seconds)
