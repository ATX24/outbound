import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    supabase_url: str
    supabase_service_role: str | None
    supabase_anon_key: str | None
    clay_api_key: str | None
    clay_webhook_url: str | None
    clay_webhook_url_bigtech: str | None
    clay_webhook_url_vc: str | None
    clay_webhook_url_ut: str | None
    firecrawl_api_key: str | None
    requests_timeout_seconds: int


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_service_role=os.getenv("SUPABASE_SERVICE_ROLE"),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY"),
        clay_api_key=os.getenv("CLAY_API_KEY"),
        clay_webhook_url=os.getenv("CLAY_WEBHOOK_URL"),
        clay_webhook_url_bigtech=os.getenv("CLAY_WEBHOOK_URL_BIGTECH"),
        clay_webhook_url_vc=os.getenv("CLAY_WEBHOOK_URL_VC"),
        clay_webhook_url_ut=os.getenv("CLAY_WEBHOOK_URL_UT"),
        firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY"),
        requests_timeout_seconds=int(os.getenv("REQUESTS_TIMEOUT_SECONDS", "30")),
    )
