from __future__ import annotations

from typing import Iterable
from common.config import load_settings
from common.clients.firecrawl_client import get_firecrawl
from common.clients.playwright_scraper import fetch_html
from common.clients.supabase_client import upsert_records
from common.clients.clay_client import get_clay_for_pipeline


def discover_team_pages(seed_urls: Iterable[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for url in seed_urls:
        html = fetch_html(url)
        results.append({"url": url, "raw_html_len": str(len(html))})
    return results


def crawl_for_signals(urls: Iterable[str]) -> list[dict[str, str]]:
    firecrawl = get_firecrawl()
    signals: list[dict[str, str]] = []
    for url in urls:
        data = firecrawl.crawl(url, limit=25)
        signals.append({"url": url, "found_items": str(len(data.get("items", [])))})
    return signals


def ingest_to_clay(records: list[dict[str, str]]) -> None:
    clay = get_clay_for_pipeline("bigtech")
    if records:
        clay.ingest_records(records)


def run_pipeline(seed_company_pages: list[str], supabase_table: str = "bigtech_signals") -> None:
    settings = load_settings()
    team_pages = discover_team_pages(seed_company_pages)
    upsert_records("bigtech_pages", team_pages)

    signals = crawl_for_signals([p["url"] for p in team_pages])
    upsert_records(supabase_table, signals)

    # Also push to Clay table for BigTech
    ingest_to_clay(signals)


if __name__ == "__main__":
    run_pipeline([
        "https://research.google/",
        "https://careers.microsoft.com/",
        "https://engineering.fb.com/",
    ])
