from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.log import get_logger
from app.supabase_client import get_service_client

logger = get_logger("cache")

TTL_HOURS: dict[tuple[int, int], int] = {
    (61, 62): 6,
    (84, 85): 24,
    (87,): 72,
}


def _get_ttl(hs_code: str | None) -> int:
    if hs_code and len(hs_code) >= 2:
        prefix = int(hs_code[:2])
        for chapters, ttl in TTL_HOURS.items():
            if prefix in chapters:
                return ttl
    return 24


def compute_query_hash(product_query: str, hs_code: str | None, destination: str) -> str:
    raw = f"{product_query.lower().strip()}|{hs_code or ''}|{destination}"
    return hashlib.md5(raw.encode()).hexdigest()


async def check_cache(query_hash: str) -> Optional[list[dict[str, Any]]]:
    supabase = get_service_client()
    if supabase is None:
        return None
    try:
        result = supabase.table("price_cached_results") \
            .select("*") \
            .eq("query_hash", query_hash) \
            .gt("expires_at", datetime.now(timezone.utc).isoformat()) \
            .order("total_landed", desc=False) \
            .execute()
        if result.data and len(result.data) > 0:
            logger.info("Cache HIT for %s (%d entries)", query_hash[:8], len(result.data))
            return result.data
    except Exception as exc:
        logger.warning("Cache check failed for %s: %s", query_hash[:8], exc)
    return None


async def write_cache(
    query_hash: str,
    product_query: str,
    hs_code: str | None,
    destination: str,
    results: list[dict[str, Any]],
) -> None:
    supabase = get_service_client()
    if supabase is None:
        return

    ttl_hours = _get_ttl(hs_code)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=ttl_hours)

    rows = []
    for r in results:
        rows.append({
            "query_hash": query_hash,
            "product_name": product_query,
            "hs_code": hs_code,
            "destination": destination,
            "origin": r.get("origin"),
            "price_original": r.get("price_original", r.get("price_usd")),
            "price_usd": r.get("price_usd"),
            "currency": r.get("currency", "USD"),
            "source_url": r.get("source_url", ""),
            "marketplace": r.get("marketplace", ""),
            "confidence": r.get("confidence", 0.5),
            "total_landed": r.get("total_landed"),
            "duty_pct": r.get("duty_pct"),
            "vat_pct": r.get("vat_pct"),
            "freight_pct": r.get("freight_pct"),
            "scraped_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        })

    if not rows:
        return

    try:
        supabase.table("price_cached_results").insert(rows).execute()
        logger.info("Cache WRITE %s (%d rows, TTL=%dh)", query_hash[:8], len(rows), ttl_hours)
    except Exception as exc:
        logger.error("Cache write failed for %s: %s", query_hash[:8], exc)
