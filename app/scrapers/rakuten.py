from __future__ import annotations

from typing import Optional

import httpx

from app.config import settings
from app.log import get_logger
from app.scrapers.base import ScrapeResult, BaseScraper

logger = get_logger("rakuten")

API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"
MAX_PRICE_JPY = 9_999_999


class RakutenScraper(BaseScraper):
    def __init__(self) -> None:
        self.app_id = settings.rakuten_app_id
        self.access_key = settings.rakuten_access_key

    @property
    def is_configured(self) -> bool:
        return bool(self.app_id and self.access_key)

    async def search(self, query: str, max_results: int = 5) -> list[ScrapeResult]:
        if not self.is_configured:
            return []

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    API_URL,
                    params={
                        "applicationId": self.app_id,
                        "accessKey": self.access_key,
                        "keyword": query,
                        "hits": max_results,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("Rakuten returned HTTP %d for '%s'", resp.status_code, query)
                    return []
                data = resp.json()
        except Exception as exc:
            logger.warning("Rakuten request failed for '%s': %s", query, exc)
            return []

        items = data.get("Items", [])
        results = []
        seen_prices: set[float] = set()

        for entry in items:
            item = entry.get("Item", {})
            price_str = item.get("itemPrice")
            if price_str is None:
                continue
            try:
                price = float(price_str)
            except (ValueError, TypeError):
                continue
            if price <= 0 or price > MAX_PRICE_JPY:
                continue
            if price in seen_prices:
                continue
            seen_prices.add(price)

            title = item.get("itemName", query)
            url = item.get("itemUrl", "")
            results.append(ScrapeResult(
                price=price,
                currency="JPY",
                product_name=title,
                source_url=url,
                marketplace="Rakuten",
                confidence=0.85,
            ))

        results.sort(key=lambda r: r.price)
        logger.info("Rakuten: %d results for '%s'", len(results), query)
        return results[:max_results]

    async def scrape(self, url: str, query: str) -> list[ScrapeResult]:
        return await self.search(query)
