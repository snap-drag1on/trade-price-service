from __future__ import annotations

from typing import Optional

from app.config import settings
from app.log import get_logger

logger = get_logger("supabase")

_client: Optional["Client"] = None
_client_service: Optional["Client"] = None


def get_supabase():
    global _client
    if _client is not None:
        return _client

    if not settings.supabase_anon_key:
        logger.warning("supabase_anon_key not set")
        return None

    from supabase import create_client

    _client = create_client(settings.supabase_url, settings.supabase_anon_key)
    logger.info("Supabase anon client created")
    return _client


def get_service_client():
    global _client_service
    if _client_service is not None:
        return _client_service

    if not settings.supabase_service_key:
        logger.warning("supabase_service_key not set")
        return None

    try:
        from supabase import create_client
        _client_service = create_client(settings.supabase_url, settings.supabase_service_key)
        logger.info("Supabase service client created")
    except Exception as e:
        logger.error("Failed to create Supabase service client: %s", e)
        return None
    return _client_service
