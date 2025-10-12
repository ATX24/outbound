from __future__ import annotations

from typing import Iterable
from common.clients.playwright_scraper import fetch_html
from common.clients.firecrawl_client import get_firecrawl
from common.clients.supabase_client import upsert_records
from common.clients.clay_client import get_clay_for_pipeline
from .signals import extract_partnership_signals


def crawl_vc_portfolios(urls: Iterable[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for url in urls:
        html = fetch_html(url)
        results.append({"portfolio_url": url, "raw_html_len": str(len(html))})
    return results


def filter_series_a_plus(companies: list[dict[str, str]]) -> list[dict[str, str]]:
    return [c for c in companies if c.get("funding_stage") in {"Series A", "Series B", "Series C", "Series D", "Series E"}]


def find_company_signals(company_domain: str, pages: list[str]) -> list[dict[str, str]]:
    firecrawl = get_firecrawl()
    signals: list[dict[str, str]] = []
    for page in pages:
        data = firecrawl.crawl(page, limit=25)
        signals.append({
            "company_domain": company_domain,
            "url": page,
            "signal_type": "CrawlItems",
            "snippet": f"items={len(data.get('items', []))}",
        })
    return signals


def ingest_to_clay(records: list[dict[str, str]]) -> None:
    clay = get_clay_for_pipeline("vc")
    if records:
        clay.ingest_records(records)


def run_pipeline(vc_portfolio_urls: list[str], supabase_tables: dict[str, str] | None = None) -> None:
    tables = supabase_tables or {
        "portfolios": "vc_portfolios",
        "companies": "portfolio_companies",
        "signals": "partnership_signals",
        "contacts": "contacts",
    }

    portfolios = crawl_vc_portfolios(vc_portfolio_urls)
    upsert_records(tables["portfolios"], portfolios)

    companies: list[dict[str, str]] = []
    filtered = filter_series_a_plus(companies)
    if filtered:
        upsert_records(tables["companies"], filtered)

    for company in filtered:
        domain = company.get("domain", "")
        if not domain:
            continue
        pages = [f"https://{domain}/partners", f"https://{domain}/community"]
        signals = find_company_signals(domain, pages)
        if signals:
            upsert_records(tables["signals"], signals)
            ingest_to_clay(signals)
