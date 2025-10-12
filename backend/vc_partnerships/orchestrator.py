from __future__ import annotations

from typing import Iterable
from common.clients.playwright_scraper import fetch_html
from common.clients.firecrawl_client import get_firecrawl
from common.clients.supabase_client import upsert_records
from common.clients.clay_client import get_clay_for_pipeline
from common.utils.filters import select_best_signals
from .signals import extract_partnership_signals
from .seed_urls import VC_PORTFOLIO_URLS


def extract_companies_from_portfolio(fund: str, url: str) -> list[dict[str, str]]:
    """Layer 1: Use Firecrawl extract to get company name/domain from portfolio page."""
    fc = get_firecrawl()
    # Ask Firecrawl to extract structured items. Options can be tuned if supported.
    res = fc.extract(url, limit=200)
    items = res.get("items") or res.get("data") or []
    companies: list[dict[str, str]] = []
    for it in items:
        name = (it.get("name") or it.get("title") or "").strip()
        domain = (it.get("domain") or it.get("url") or "").strip()
        if not name and not domain:
            continue
        companies.append({
            "name": name,
            "domain": domain.replace("https://", "").replace("http://", "").strip("/"),
            "fund": fund,
            "portfolio_url": url,
        })
    return companies


def crawl_company_signals(company_domain: str) -> list[dict[str, str]]:
    """Layer 2: Crawl the company site for specific partnership signals."""
    fc = get_firecrawl()
    pages = [
        f"https://{company_domain}",
        f"https://{company_domain}/partners",
        f"https://{company_domain}/community",
        f"https://{company_domain}/university",
        f"https://{company_domain}/research",
    ]
    signals: list[dict[str, str]] = []
    for page in pages:
        data = fc.crawl(page, limit=15)
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


def run_pipeline(vc_portfolio_urls: list[tuple[str, str]] | None = None, supabase_tables: dict[str, str] | None = None) -> None:
    tables = supabase_tables or {
        "portfolios": "vc_portfolios",
        "companies": "portfolio_companies",
        "signals": "partnership_signals",
        "contacts": "contacts",
    }

    seeds = vc_portfolio_urls or VC_PORTFOLIO_URLS

    # Layer 1: Extract companies from each fund's portfolio page
    all_companies: list[dict[str, str]] = []
    for fund, url in seeds:
        companies = extract_companies_from_portfolio(fund, url)
        all_companies.extend(companies)
    if all_companies:
        upsert_records(tables["companies"], all_companies)

    # Layer 2: For each company domain, crawl for signals
    all_signals: list[dict[str, str]] = []
    for c in all_companies:
        domain = c.get("domain")
        if not domain:
            continue
        sigs = crawl_company_signals(domain)
        all_signals.extend(sigs)

    if all_signals:
        upsert_records(tables["signals"], all_signals)
        best = select_best_signals(all_signals)
        ingest_to_clay(best)
