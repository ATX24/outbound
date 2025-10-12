from __future__ import annotations

from typing import Iterable
from common.clients.playwright_scraper import fetch_html
from common.clients.firecrawl_client import get_firecrawl
from common.clients.supabase_client import upsert_records
from common.clients.clay_client import get_clay_for_pipeline
from .signals import extract_donor_signals


def crawl_ut_sources(urls: Iterable[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for url in urls:
        html = fetch_html(url)
        results.append({"url": url, "raw_html_len": str(len(html))})
    return results


def discover_donor_signals(urls: Iterable[str]) -> list[dict[str, str]]:
    firecrawl = get_firecrawl()
    signals: list[dict[str, str]] = []
    for url in urls:
        crawl = firecrawl.crawl(url, limit=25)
        signals.append({"url": url, "snippet": f"items={len(crawl.get('items', []))}", "tag": "Crawl"})
    return signals


def ingest_to_clay(records: list[dict[str, str]]) -> None:
    clay = get_clay_for_pipeline("ut")
    if records:
        clay.ingest_records(records)


def run_pipeline(ut_urls: list[str], supabase_tables: dict[str, str] | None = None) -> None:
    tables = supabase_tables or {
        "pages": "ut_pages",
        "signals": "ut_donor_signals",
        "contacts": "contacts",
    }
    pages = crawl_ut_sources(ut_urls)
    upsert_records(tables["pages"], pages)

    signals = discover_donor_signals([p["url"] for p in pages])
    if signals:
        upsert_records(tables["signals"], signals)
        ingest_to_clay(signals)
