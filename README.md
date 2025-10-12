# Outbound Pipelines (Python)

This repo discovers collaboration/opportunity signals from Big Tech, VC portfolios, and UT alumni sources, stores everything in a central database (Supabase/Postgres), and forwards only the highest‑quality signals to Clay for enrichment and outreach.

## What it does
- Crawls target pages (Playwright + Firecrawl) to find signals like research portals, partnerships, hackathons, RFPs, donor mentions.
- Writes all raw/processed records to Supabase as the source of truth.
- Selects “best” signals and posts those into per‑pipeline Clay tables via inbound webhooks.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install
```

Environment variables (store locally in env/dev.env or your secret manager):
- Supabase: SUPABASE_URL, SUPABASE_SERVICE_ROLE (or ANON key with proper RLS)
- Firecrawl: FIRECRAWL_API_KEY
- Clay: CLAY_WEBHOOK_URL_BIGTECH, CLAY_WEBHOOK_URL_VC, CLAY_WEBHOOK_URL_UT (+ CLAY_API_KEY if webhook auth enabled)
- REQUESTS_TIMEOUT_SECONDS (optional)

Create database tables by running the SQL in `backend/db/schema.sql` in Supabase (SQL editor).

## Run
- Big Tech: `python -m backend.bigtech --table bigtech_signals`
- VC: `python -m backend.vc_partnerships --portfolios-table vc_portfolios --companies-table portfolio_companies --signals-table partnership_signals`
- UT: `python -m backend.ut_alumni --pages-table ut_pages --signals-table ut_donor_signals`

Notes
- Keep credentials in environment variables only (not in this repo).
- Each pipeline should point to its own Clay table webhook.
- Tune the heuristics and filtering under `backend/**/signals.py` and `backend/common/utils/filters.py` for your needs.
