from __future__ import annotations

import time
from typing import Optional

import httpx

from app.config import settings
from app.log import get_logger
from app.scrapers.base import ScrapeResult, BaseScraper

logger = get_logger("ebay")

MARKETPLACE_MAP: dict[str, dict] = {
    "US": {"id": "EBAY_US", "domain": "ebay.com", "currency": "USD"},
    "DE": {"id": "EBAY_DE", "domain": "ebay.de", "currency": "EUR"},
    "GB": {"id": "EBAY_GB", "domain": "ebay.co.uk", "currency": "GBP"},
    "FR": {"id": "EBAY_FR", "domain": "ebay.fr", "currency": "EUR"},
    "IT": {"id": "EBAY_IT", "domain": "ebay.it", "currency": "EUR"},
    "ES": {"id": "EBAY_ES", "domain": "ebay.es", "currency": "EUR"},
    "AU": {"id": "EBAY_AU", "domain": "ebay.com.au", "currency": "AUD"},
    "CA": {"id": "EBAY_CA", "domain": "ebay.ca", "currency": "CAD"},
}


class EbayBrowseApiScraper(BaseScraper):
    def __init__(self) -> None:
        self.app_id = settings.ebay_app_id
        self.cert_id = settings.ebay_cert_id
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    @property
    def is_configured(self) -> bool:
        return bool(self.app_id and self.cert_id)

    async def _get_token(self) -> Optional[str]:
        if self._token and time.time() < self._token_expires_at:
            return self._token

        if not self.is_configured:
            return None

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.ebay.com/identity/v1/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "scope": "https://api.ebay.com/oauth/api_scope/buy.browse",
                    },
                    auth=(self.app_id, self.cert_id),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if resp.status_code != 200:
                    logger.warning("eBay OAuth failed: HTTP %d", resp.status_code)
                    return None
                data = resp.json()
                self._token = data.get("access_token")
                expires_in = data.get("expires_in", 7200)
                self._token_expires_at = time.time() + expires_in - 60
                logger.info("eBay OAuth token refreshed")
                return self._token
        except Exception as exc:
            logger.warning("eBay OAuth error: %s", exc)
            return None

    async def search(self, query: str, country: str) -> list[ScrapeResult]:
        token = await self._get_token()
        if token is None:
            return []

        mp = MARKETPLACE_MAP.get(country.upper())
        if mp is None:
            logger.warning("eBay marketplace %s not supported", country)
            return []

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.ebay.com/buy/browse/v1/item_summary/search",
                    params={"q": query, "limit": 5},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-EBAY-C-MARKETPLACE-ID": mp["id"],
                        "X-EBAY-C-ENDUSERCTX": "contextualLocation=country=" + country,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("eBay search failed: HTTP %d for %s", resp.status_code, country)
                    return []

                data = resp.json()
                items = data.get("itemSummaries", [])
                results = []
                seen_prices: set[float] = set()

                for item in items:
                    price_data = (item.get("price") or
                                  (item.get("sellerItemRevision") or {}).get("price") or
                                  {})
                    value = price_data.get("value")
                    currency = price_data.get("currency", mp["currency"])
                    if value is None:
                        continue
                    try:
                        price = float(value)
                    except (ValueError, TypeError):
                        continue

                    if price < 0.1 or price > 9_999_999:
                        continue
                    if price in seen_prices:
                        continue
                    seen_prices.add(price)

                    title = item.get("title", query)
                    url = item.get("itemWebUrl", "")
                    results.append(ScrapeResult(
                        price=price,
                        currency=currency.upper(),
                        product_name=title,
                        source_url=url,
                        marketplace=f"eBay {mp['id']}",
                        confidence=0.9,
                    ))

                results.sort(key=lambda r: r.price)
                logger.info("eBay %s: found %d results for '%s'", country, len(results), query)
                return results[:3]
        except Exception as exc:
            logger.warning("eBay search error for %s: %s", country, exc)
            return []

    async def scrape(self, url: str, query: str) -> list[ScrapeResult]:
        return await self.search(query, "US")
