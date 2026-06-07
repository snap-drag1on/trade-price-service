from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.cache import compute_query_hash, check_cache, write_cache
from app.currency import convert_to_usd
from app.landed_cost import calculate_landed_cost
from app.log import get_logger
from app.scrapers import PlaywrightScraper, EbayBrowseApiScraper, ApifyAliExpressScraper, RakutenScraper
from app.supabase_client import get_supabase
from app.demo_data import load_demo_data

logger = get_logger("search")

router = APIRouter()
scraper = PlaywrightScraper()
ebay_scraper = EbayBrowseApiScraper()
apify_scraper = ApifyAliExpressScraper()
rakuten_scraper = RakutenScraper()


class SearchRequest(BaseModel):
    product_query: str = Field(..., min_length=1, description="Product name to search")
    hs_code: Optional[str] = Field(None, description="HS code (6 digits)")
    destination: str = Field(..., min_length=2, max_length=2, description="Destination country code")
    transport_mode: str = Field(default="rail", pattern="^(rail|air|sea|road)$")
    max_origins: int = Field(default=6, ge=1, le=10)
    mode: str = Field(default="auto", pattern="^(auto|live|demo)$",
                      description="auto=try live then fallback, live=scrape only, demo=skip scrape")


class OriginResult(BaseModel):
    origin: str
    marketplace: str
    product_name: str
    price_original: float
    currency: str
    price_usd: float
    duty_pct: float
    vat_pct: float
    freight_pct: float
    total_landed: float
    effective_rate_pct: float
    confidence: float
    source_url: str


class SearchResponse(BaseModel):
    query: dict
    results: list[OriginResult]
    decision: Optional[dict] = None
    cache_hit: bool = False
    elapsed_ms: float = 0.0
    source: str = "demo"
    note: Optional[str] = None
    ebay_used: bool = False
    apify_used: bool = False
    rakuten_used: bool = False


ORIGIN_TIMEOUT = 25


async def _call_api_search_sourcing(
    hs_code: str | None,
    destination: str,
) -> list[dict[str, Any]]:
    supabase = get_supabase()
    if supabase is None:
        return []
    try:
        data = supabase.rpc(
            "api_search_sourcing",
            {
                "cif_value": 100,
                "destination": destination,
                "hs_code": hs_code or "",
                "product_query": "",
                "transport_mode": "rail",
            },
        ).execute()
        if data.data and isinstance(data.data, dict):
            results = data.data.get("results", [])
            if isinstance(results, list):
                return results
        return []
    except Exception as exc:
        logger.warning("api_search_sourcing RPC failed: %s", exc)
        return []


async def _to_result(
    sr, origin: str, marketplace: str, product_query: str, url: str,
    duty_pct: float, vat_pct: float, freight_pct: float,
) -> OriginResult:
    price_usd = convert_to_usd(sr.price, sr.currency)
    landed = calculate_landed_cost(price_usd, duty_pct, vat_pct, freight_pct)
    return OriginResult(
        origin=origin,
        marketplace=sr.marketplace or marketplace,
        product_name=sr.product_name or product_query,
        price_original=round(sr.price, 2),
        currency=sr.currency,
        price_usd=landed.price_usd,
        duty_pct=duty_pct,
        vat_pct=vat_pct,
        freight_pct=freight_pct,
        total_landed=landed.total_landed,
        effective_rate_pct=landed.effective_rate_pct,
        confidence=sr.confidence,
        source_url=sr.source_url or url,
    )


async def _try_ebay(
    origin: str,
    product_query: str,
    duty_pct: float,
    vat_pct: float,
    freight_pct: float,
) -> OriginResult | None:
    if not ebay_scraper.is_configured:
        return None
    if origin.upper() not in ("US", "DE", "GB"):
        return None
    try:
        results = await asyncio.wait_for(
            ebay_scraper.search(product_query, origin), timeout=10,
        )
    except Exception as exc:
        logger.debug("eBay scrape failed for %s/%s: %s", origin, product_query, exc)
        return None
    if not results:
        return None
    best = results[0]
    return await _to_result(
        best, origin, f"eBay {origin}", product_query, best.source_url,
        duty_pct, vat_pct, freight_pct,
    )


async def _try_apify(
    origin: str,
    product_query: str,
    duty_pct: float,
    vat_pct: float,
    freight_pct: float,
) -> OriginResult | None:
    if not apify_scraper.is_configured:
        return None
    if origin.upper() != "CN":
        return None
    try:
        results = await asyncio.wait_for(
            apify_scraper.search(product_query), timeout=25,
        )
    except Exception as exc:
        logger.debug("Apify scrape failed for '%s': %s", product_query, exc)
        return None
    if not results:
        return None
    best = results[0]
    return await _to_result(
        best, origin, "AliExpress", product_query, best.source_url,
        duty_pct, vat_pct, freight_pct,
    )


async def _try_rakuten(
    origin: str,
    product_query: str,
    duty_pct: float,
    vat_pct: float,
    freight_pct: float,
) -> OriginResult | None:
    if not rakuten_scraper.is_configured:
        return None
    if origin.upper() != "JP":
        return None
    try:
        results = await asyncio.wait_for(
            rakuten_scraper.search(product_query), timeout=10,
        )
    except Exception as exc:
        logger.debug("Rakuten scrape failed for '%s': %s", product_query, exc)
        return None
    if not results:
        return None
    best = results[0]
    return await _to_result(
        best, origin, "Rakuten", product_query, best.source_url,
        duty_pct, vat_pct, freight_pct,
    )


async def _scrape_origin(
    origin_info: dict[str, Any],
    product_query: str,
    use_ebay: bool = True,
) -> OriginResult | None:
    origin = origin_info.get("origin", "")
    trade_costs = origin_info.get("trade_costs", {})
    marketplaces = origin_info.get("marketplaces_to_search", origin_info.get("marketplaces", []))

    duty_pct = float(trade_costs.get("duty_rate_pct", 0))
    vat_pct = float(trade_costs.get("vat_rate_pct", 0))
    freight_pct = float(trade_costs.get("freight_rate_pct", 15))

    if use_ebay:
        ebay_result = await _try_ebay(origin, product_query, duty_pct, vat_pct, freight_pct)
        if ebay_result is not None:
            return ebay_result

    apify_result = await _try_apify(origin, product_query, duty_pct, vat_pct, freight_pct)
    if apify_result is not None:
        return apify_result

    rakuten_result = await _try_rakuten(origin, product_query, duty_pct, vat_pct, freight_pct)
    if rakuten_result is not None:
        return rakuten_result

    best_result: Optional[OriginResult] = None

    for mp in marketplaces:
        template = mp.get("search_url_template", "")
        if not template:
            continue
        url = template.replace("{query}", product_query.replace(" ", "+"))

        try:
            scrape_results = await asyncio.wait_for(
                scraper.scrape(url, product_query), timeout=ORIGIN_TIMEOUT,
            )
        except (asyncio.TimeoutError, Exception):
            continue

        for sr in scrape_results:
            result = await _to_result(
                sr, origin, mp.get("name", ""), product_query, url,
                duty_pct, vat_pct, freight_pct,
            )
            if best_result is None or result.total_landed < best_result.total_landed:
                best_result = result

    if best_result is None:
        fallback_urls = {
            "US": f"https://www.etsy.com/search?q={product_query.replace(' ', '+')}",
            "DE": f"https://www.etsy.com/de/search?q={product_query.replace(' ', '+')}",
            "GB": f"https://www.etsy.com/uk/search?q={product_query.replace(' ', '+')}",
            "FR": f"https://www.etsy.com/fr/search?q={product_query.replace(' ', '+')}",
        }
        fb_url = fallback_urls.get(origin.upper())
        if fb_url:
            try:
                fb_results = await asyncio.wait_for(
                    scraper.scrape(fb_url, product_query), timeout=ORIGIN_TIMEOUT,
                )
            except (asyncio.TimeoutError, Exception):
                fb_results = []
            for sr in fb_results:
                result = await _to_result(
                    sr, origin, "Etsy", product_query, fb_url,
                    duty_pct, vat_pct, freight_pct,
                )
                if best_result is None or result.total_landed < best_result.total_landed:
                    best_result = result

    return best_result


def _build_decision(results: list[OriginResult]) -> Optional[dict[str, Any]]:
    if not results:
        return None
    best = results[0]
    runner_up = results[1] if len(results) > 1 else None
    savings = (runner_up.total_landed - best.total_landed) if runner_up else 0.0
    return {
        "best_origin": best.origin,
        "best_marketplace": best.marketplace,
        "best_price": best.price_usd,
        "best_landed": best.total_landed,
        "savings_vs_next": round(savings, 2),
        "total_origins_checked": len(results),
    }


def _demo_to_result(item: dict, product_query: str) -> OriginResult:
    price_usd = convert_to_usd(item["price_original"], item["currency"])
    landed = calculate_landed_cost(
        price_usd, item["duty_pct"], item["vat_pct"], item["freight_pct"],
    )
    return OriginResult(
        origin=item["origin"],
        marketplace=item["marketplace"],
        product_name=product_query,
        price_original=item["price_original"],
        currency=item["currency"],
        price_usd=landed.price_usd,
        duty_pct=item["duty_pct"],
        vat_pct=item["vat_pct"],
        freight_pct=item["freight_pct"],
        total_landed=landed.total_landed,
        effective_rate_pct=landed.effective_rate_pct,
        confidence=0.6,
        source_url="",
    )


@router.post("/search", response_model=SearchResponse)
async def search_prices(req: SearchRequest) -> SearchResponse:
    start = datetime.now(timezone.utc)
    query_hash = compute_query_hash(req.product_query, req.hs_code, req.destination)

    cached = await check_cache(query_hash)
    if cached is not None:
        results = []
        for r in cached:
            results.append(OriginResult(
                origin=r.get("origin", ""),
                marketplace=r.get("marketplace", ""),
                product_name=r.get("product_name", req.product_query),
                price_original=float(r.get("price_original", r.get("price_usd", 0))),
                currency=r.get("currency", "USD"),
                price_usd=float(r.get("price_usd", 0)),
                duty_pct=float(r.get("duty_pct", 0)),
                vat_pct=float(r.get("vat_pct", 0)),
                freight_pct=float(r.get("freight_pct", 0)),
                total_landed=float(r.get("total_landed", 0)),
                effective_rate_pct=float(r.get("effective_rate_pct", 0)),
                confidence=float(r.get("confidence", 0.5)),
                source_url=r.get("source_url", ""),
            ))
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        apify_used = any("aliexpress" in r.marketplace.lower() for r in results)
        rakuten_used = any("rakuten" in r.marketplace.lower() for r in results)
        return SearchResponse(
            query=req.model_dump(), results=sorted(results, key=lambda r: r.total_landed),
            decision=_build_decision(results), cache_hit=True, elapsed_ms=round(elapsed, 1),
            apify_used=apify_used,
            rakuten_used=rakuten_used,
        )

    note = None
    source = "live"
    results = []
    ebay_used = False
    apify_used = False
    rakuten_used = False

    if req.mode == "demo":
        demo_items = load_demo_data(req.hs_code, req.product_query, req.max_origins)
        results = [_demo_to_result(item, req.product_query) for item in demo_items]
        source = "demo"
        note = "Demo data — no real prices scraped"

    elif req.mode == "live":
        origins_info = await _call_api_search_sourcing(req.hs_code, req.destination)
        if not origins_info:
            raise HTTPException(status_code=502, detail="Supabase not available — cannot source origins")
        origins_info = origins_info[:req.max_origins]
        tasks = [_scrape_origin(oi, req.product_query, use_ebay=True) for oi in origins_info]
        scraped = await asyncio.gather(*tasks)
        results = [r for r in scraped if r is not None]
        ebay_used = ebay_scraper.is_configured and any(
            "ebay" in r.marketplace.lower() for r in results
        )
        apify_used = apify_scraper.is_configured and any(
            "aliexpress" in r.marketplace.lower() for r in results
        )
        rakuten_used = rakuten_scraper.is_configured and any(
            "rakuten" in r.marketplace.lower() for r in results
        )
        if not results:
            raise HTTPException(status_code=502, detail="All origins failed to scrape — no prices found")

    else:  # auto — merge live + demo for complete comparison
        origins_info = await _call_api_search_sourcing(req.hs_code, req.destination)
        live_origins: dict[str, OriginResult] = {}
        if origins_info:
            origins_info = origins_info[:req.max_origins]
            tasks = [_scrape_origin(oi, req.product_query, use_ebay=True) for oi in origins_info]
            scraped = await asyncio.gather(*tasks)
            for r in scraped:
                if r is not None:
                    live_origins[r.origin] = r

        demo_items = load_demo_data(req.hs_code, req.product_query, req.max_origins)
        results = []
        seen_origins: set[str] = set()
        for item in demo_items:
            origin = item["origin"]
            seen_origins.add(origin)
            if origin in live_origins:
                results.append(live_origins[origin])
            else:
                results.append(_demo_to_result(item, req.product_query))

        for origin, r in live_origins.items():
            if origin not in seen_origins:
                results.append(r)

        ebay_used = ebay_scraper.is_configured and any(
            "ebay" in r.marketplace.lower() for r in results
        )
        apify_used = apify_scraper.is_configured and any(
            "aliexpress" in r.marketplace.lower() for r in results
        )
        rakuten_used = rakuten_scraper.is_configured and any(
            "rakuten" in r.marketplace.lower() for r in results
        )
        source = "live" if live_origins else "demo"
        if live_origins and len(live_origins) < len(results):
            note = f"Merged: {len(live_origins)} live + {len(results) - len(live_origins)} estimated origins"
        elif not live_origins:
            note = "Scraping unavailable — demo data shown"
            source = "demo"

    results.sort(key=lambda r: r.total_landed)

    await write_cache(
        query_hash, req.product_query, req.hs_code, req.destination,
        [r.model_dump() for r in results],
    )

    elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    return SearchResponse(
        query=req.model_dump(), results=results,
        decision=_build_decision(results), cache_hit=False,
        elapsed_ms=round(elapsed, 1), source=source, note=note,
        ebay_used=ebay_used,
        apify_used=apify_used,
        rakuten_used=rakuten_used,
    )
