from __future__ import annotations

import argparse
from .seed_urls import UT_SEED_URLS
from .orchestrator import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run UT Alumni pipeline")
    parser.add_argument("--url", action="append", help="UT seed URL(s)")
    parser.add_argument("--pages-table", default="ut_pages")
    parser.add_argument("--signals-table", default="ut_donor_signals")
    parser.add_argument("--contacts-table", default="contacts")
    args = parser.parse_args()

    urls = list(UT_SEED_URLS)
    if args.url:
        urls.extend(args.url)

    tables = {
        "pages": args.pages_table,
        "signals": args.signals_table,
        "contacts": args.contacts_table,
    }

    run_pipeline(urls, supabase_tables=tables)


if __name__ == "__main__":
    main()
