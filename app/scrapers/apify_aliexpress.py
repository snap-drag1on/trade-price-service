from __future__ import annotations

from typing import Optional

import httpx

from app.config import settings
from app.log import get_logger
from app.scrapers.base import ScrapeResult, BaseScraper

logger = get_logger("apify")

ACTOR_ID = "devcake~aliexpress-products-scraper"
API_BASE = "https://api.apify.com/v2"
MIN_PRICE = 1.0
MAX_PRICE = 99_999.0


class ApifyAliExpressScraper(BaseScraper):
    def __init__(self) -> None:
        self.token = settings.apify_token

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    async def search(self, query: str, max_results: int = 5) -> list[ScrapeResult]:
        if not self.is_configured:
            return []

        url = f"{API_BASE}/acts/{ACTOR_ID}/run-sync-get-dataset-items?token={self.token}"
        payload = {
            "searchQueries": [query],
            "maxPages": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 401:
                    logger.warning("Apify token expired/revoked for '%s' — CN prices via Apify broken", query)
                    return []
                if resp.status_code not in (200, 201):
                    logger.warning("Apify returned HTTP %d for '%s'", resp.status_code, query)
                    return []
                items = resp.json()
        except Exception as exc:
            logger.warning("Apify request failed for '%s': %s", query, exc)
            return []

        results = []
        seen_prices: set[float] = set()
        for item in items:
            price = item.get("priceCurrentMin")
            if price is None:
                continue
            try:
                price_f = float(price)
            except (ValueError, TypeError):
                continue
            if price_f < MIN_PRICE or price_f > MAX_PRICE:
                continue
            if price_f in seen_prices:
                continue
            seen_prices.add(price_f)

            title = item.get("title", query)
            product_url = item.get("productUrl", "")
            results.append(ScrapeResult(
                price=price_f,
                currency="USD",
                product_name=title,
                source_url=product_url,
                marketplace="AliExpress",
                confidence=0.85,
            ))

        results.sort(key=lambda r: r.price)
        logger.info("Apify: %d results for '%s'", len(results), query)
        return results[:max_results]

    async def scrape(self, url: str, query: str) -> list[ScrapeResult]:
        return await self.search(query)
