from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import field_validator


# Public anon key for trade-price-service Supabase project (safe to embed)
_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wd29qcXFlZXJlbmJ2Z2t2bnlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAwOTcwMjksImV4cCI6MjA5NTY3MzAyOX0.2H3YscM7O7n5I9Wj9KFVDdm3I-A7FMSf9XrVxmIYBms"


class Settings(BaseSettings):
    supabase_url: str = "https://npwojqqeerenbvgkvnyd.supabase.co"
    supabase_service_key: str = ""
    supabase_anon_key: str = _ANON_KEY  # env override; fallback to embedded if truncated

    @field_validator("supabase_anon_key")
    @classmethod
    def _fix_truncated_key(cls, v: str) -> str:
        if len(v) < 100:
            return _ANON_KEY
        return v
    ebay_app_id: str = ""
    ebay_cert_id: str = ""
    apify_token: str = ""
    rakuten_app_id: str = ""
    rakuten_access_key: str = ""
    openrouter_api_key: str = ""
    google_api_key: str = ""
    nvbuild_api_key: str = ""
    github_pat: str = ""
    csk_key: str = ""
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


def validate_config() -> list[str]:
    warnings: list[str] = []
    if not settings.supabase_anon_key:
        warnings.append("SUPABASE_ANON_KEY not set — RPC calls will fail")
    if not settings.supabase_service_key:
        warnings.append("SUPABASE_SERVICE_KEY not set — cache will not persist")
    if not settings.apify_token:
        warnings.append("APIFY_TOKEN not set — CN (AliExpress) prices unavailable")
    if not settings.rakuten_app_id or not settings.rakuten_access_key:
        warnings.append("RAKUTEN_APP_ID/ACCESS_KEY not set — JP (Rakuten) prices unavailable")
    if not settings.nvbuild_api_key and not settings.github_pat:
        warnings.append("NVBUILD_API_KEY or GITHUB_PAT not set — AI agent unavailable")
    return warnings
