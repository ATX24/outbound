from __future__ import annotations

from typing import Any
from supabase import create_client, Client
from ..config import load_settings


_supabase_client: Client | None = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        settings = load_settings()
        if not settings.supabase_url or not (settings.supabase_service_role or settings.supabase_anon_key):
            raise RuntimeError("Supabase URL and a key must be set in environment")
        key = settings.supabase_service_role or settings.supabase_anon_key  # prefer service role for writes
        _supabase_client = create_client(settings.supabase_url, key)  # type: ignore[arg-type]
    return _supabase_client


def upsert_records(table: str, rows: list[dict[str, Any]]) -> None:
    client = get_supabase()
    if not rows:
        return
    response = client.table(table).upsert(rows).execute()
    if getattr(response, "error", None):
        raise RuntimeError(f"Supabase upsert error: {response.error}")
