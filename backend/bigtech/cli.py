from __future__ import annotations

import argparse
from .orchestrator import run_pipeline
from .seed_urls import SEED_COMPANY_PAGES


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BigTech signal discovery pipeline")
    parser.add_argument("--table", default="bigtech_signals", help="Supabase table to upsert into")
    parser.add_argument("--url", action="append", help="Seed URL(s) to include in addition to defaults")
    args = parser.parse_args()

    seeds = list(SEED_COMPANY_PAGES)
    if args.url:
        seeds.extend(args.url)

    run_pipeline(seeds, supabase_table=args.table)


if __name__ == "__main__":
    main()
