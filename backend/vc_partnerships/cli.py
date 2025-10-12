from __future__ import annotations

import argparse
from .seed_urls import VC_PORTFOLIO_URLS
from .orchestrator import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VC Partnerships pipeline")
    parser.add_argument("--portfolio-url", action="append", help="VC portfolio URL(s)")
    parser.add_argument("--portfolios-table", default="vc_portfolios")
    parser.add_argument("--companies-table", default="portfolio_companies")
    parser.add_argument("--signals-table", default="partnership_signals")
    parser.add_argument("--contacts-table", default="contacts")
    args = parser.parse_args()

    urls = list(VC_PORTFOLIO_URLS)
    if args.portfolio_url:
        urls.extend(args.portfolio_url)

    tables = {
        "portfolios": args.portfolios_table,
        "companies": args.companies_table,
        "signals": args.signals_table,
        "contacts": args.contacts_table,
    }

    run_pipeline(urls, supabase_tables=tables)


if __name__ == "__main__":
    main()
