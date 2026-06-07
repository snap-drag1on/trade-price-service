from __future__ import annotations

import json
import re
import random

from playwright.async_api import async_playwright

from app.log import get_logger
from app.scrapers.base import ScrapeResult, BaseScraper

logger = get_logger("playwright")

_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

PRICE_REGEX = re.compile(
    r'(\$|EUR|€|GBP|£|CNY|¥|₩|₽|₺|AED|د\.إ|INR|₹)\s*(\d+[.,]?\d*)',
    re.IGNORECASE,
)

CURRENCY_MAP = {
    "$": "USD", "EUR": "EUR", "€": "EUR",
    "£": "GBP", "GBP": "GBP",
    "CNY": "CNY", "¥": "CNY",
    "₩": "KRW", "₽": "RUB", "₺": "TRY",
    "AED": "AED", "₹": "INR",
    "د.إ": "AED", "INR": "INR",
}


class PlaywrightScraper(BaseScraper):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def scrape(self, url: str, query: str) -> list[ScrapeResult]:
        logger.info("Scraping %s for '%s'", url.split("/")[2] if "//" in url else url, query)
        p = await async_playwright().start()
        browser = None
        try:
            ua = random.choice(_USER_AGENTS)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            ctx = await browser.new_context(
                user_agent=ua,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            page = await ctx.new_page()
            try:
                await page.goto(url, timeout=20000, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                results = await self._extract_all(page, query, url)
                logger.debug("Found %d results from %s", len(results), url.split("/")[2] if "//" in url else url)
                return results
            except Exception as exc:
                logger.warning("Page scrape failed for %s: %s", url.split("/")[2] if "//" in url else url[:60], exc)
                return []
            finally:
                try:
                    await page.close()
                except Exception:
                    pass
                try:
                    await ctx.close()
                except Exception:
                    pass
        except Exception as exc:
            logger.warning("Browser launch failed: %s", exc)
            return []
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            try:
                await p.stop()
            except Exception:
                pass

    async def _extract_all(self, page, query: str, url: str) -> list[ScrapeResult]:
        results = []
        site_name = self._get_marketplace_name(url)
        if site_name == "Etsy":
            results = await self._extract_etsy(page)
        elif site_name == "Alibaba":
            results = await self._extract_alibaba(page)
        if not results:
            results = await self._extract_jsonld(page)
        if not results:
            meta = await self._extract_meta_price(page)
            if meta:
                results.append(meta)
        if not results:
            results = await self._extract_dom_prices(page)
        if not results:
            text = await page.evaluate("() => document.body?.innerText || ''")
            results = self._extract_from_text(text, query)
        if not results:
            html = await page.content()
            results = self._extract_from_text(html, query)
        for r in results:
            r.source_url = url
            r.marketplace = site_name
        return results

    async def _extract_etsy(self, page) -> list[ScrapeResult]:
        return await page.evaluate("""
            () => {
                const items = [];
                document.querySelectorAll('[data-listing-id]').forEach(el => {
                    const priceEl = el.querySelector('.currency-value, .currency-value-lg, .native-currency-value');
                    const titleEl = el.querySelector('h3, .v2-listing-card__title, .listing-title');
                    if (priceEl) {
                        const text = priceEl.innerText.trim();
                        const match = text.match(/[\\d,.]+/);
                        if (match) {
                            items.push({
                                price: parseFloat(match[0].replace(/,/g, '')),
                                currency: 'USD',
                                product_name: titleEl ? titleEl.innerText.trim() : '',
                                confidence: 0.7
                            });
                        }
                    }
                });
                return items.slice(0, 5);
            }
        """)

    async def _extract_alibaba(self, page) -> list[ScrapeResult]:
        return await page.evaluate("""
            () => {
                const items = [];
                document.querySelectorAll('[class*=\"organic-list\"] [class*=\"price\"], .item-main, .list-item').forEach(el => {
                    const text = el.innerText;
                    const match = text.match(/\\$\\s*([\\d,.]+)/);
                    if (match) {
                        items.push({
                            price: parseFloat(match[1].replace(/,/g, '')),
                            currency: 'USD',
                            product_name: (el.querySelector('[class*=\"title\"], a')?.innerText || '').trim().slice(0, 100),
                            confidence: 0.65
                        });
                    }
                });
                return items.slice(0, 5);
            }
        """)

    async def _extract_dom_prices(self, page) -> list[ScrapeResult]:
        return await page.evaluate("""
            () => {
                const results = [];
                const visited = new Set();
                const selectors = [
                    '[class*=\"price\"]', '[class*=\"Price\"]',
                    '[data-price]', '[itemprop=\"price\"]',
                    '.currency-value', '.a-price',
                    '[data-testid=\"price\"]'
                ];
                for (const sel of selectors) {
                    for (const el of document.querySelectorAll(sel)) {
                        const text = el.innerText || el.getAttribute('content') || '';
                        const match = text.match(/\\$?\\s*([\\d,.]+)/);
                        if (match) {
                            const val = parseFloat(match[1].replace(/,/g, ''));
                            if (val > 0.1 && val < 100000 && !visited.has(val)) {
                                visited.add(val);
                                results.push({
                                    price: val,
                                    currency: text.includes('€') ? 'EUR' : text.includes('£') ? 'GBP' : 'USD',
                                    product_name: '',
                                    confidence: 0.5
                                });
                            }
                        }
                    }
                }
                return results.slice(0, 5);
            }
        """)

    async def _extract_jsonld(self, page) -> list[ScrapeResult]:
        results = []
        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        for el in scripts:
            try:
                text = await el.text_content()
                if not text:
                    continue
                data = json.loads(text)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and item.get("@type") in (
                        "Product", "ItemList", "Offer", "AggregateOffer",
                    ):
                        offers = item.get("offers", item)
                        if isinstance(offers, dict):
                            self._parse_offer(offers, item, results)
                        elif isinstance(offers, list):
                            for o in offers:
                                self._parse_offer(o, item, results)
            except Exception as exc:
                logger.debug("JSON-LD parse error: %s", exc)
                continue
        return results

    def _parse_offer(self, offer: dict, parent: dict, results: list[ScrapeResult]) -> None:
        price = offer.get("price") or offer.get("lowPrice")
        currency = offer.get("priceCurrency", "USD")
        name = parent.get("name", "")
        if price is not None:
            try:
                results.append(ScrapeResult(
                    price=float(price),
                    currency=currency.upper(),
                    product_name=name,
                    confidence=0.85,
                ))
            except (ValueError, TypeError):
                pass

    async def _extract_meta_price(self, page) -> ScrapeResult | None:
        price = await page.evaluate("""
            () => {
                const m = document.querySelector('meta[property="product:price:amount"]');
                return m ? m.getAttribute('content') : null;
            }
        """)
        currency = await page.evaluate("""
            () => {
                const m = document.querySelector('meta[property="product:price:currency"]');
                return m ? m.getAttribute('content') : 'USD';
            }
        """)
        name = await page.evaluate("""
            () => {
                const m = document.querySelector('meta[property="og:title"]');
                return m ? m.getAttribute('content') : '';
            }
        """)
        if price:
            try:
                return ScrapeResult(
                    price=float(price),
                    currency=currency.upper(),
                    product_name=name or "",
                    confidence=0.7,
                )
            except (ValueError, TypeError):
                pass
        return None

    def _extract_from_text(self, text: str, query: str) -> list[ScrapeResult]:
        results = []
        seen = set()
        for match in PRICE_REGEX.finditer(text):
            raw = match.group(0)
            if raw in seen:
                continue
            seen.add(raw)
            try:
                num = float(match.group(2).replace(",", ""))
                if num < 0.1 or num > 1_000_000:
                    continue
                currency = "USD"
                for sym, code in CURRENCY_MAP.items():
                    if sym in raw:
                        currency = code
                        break
                results.append(ScrapeResult(
                    price=num, currency=currency, product_name=query, confidence=0.35,
                ))
            except (ValueError, IndexError):
                continue
        results.sort(key=lambda r: r.price)
        return results[:3]

    def _get_marketplace_name(self, url: str) -> str:
        domain = url.lower()
        if "google.com/search" in domain:
            return "Google Shopping"
        if "amazon" in domain:
            return "Amazon"
        if "ebay" in domain:
            return "eBay"
        if "aliexpress" in domain:
            return "AliExpress"
        if "alibaba" in domain:
            return "Alibaba"
        if "trendyol" in domain:
            return "Trendyol"
        if "coupang" in domain:
            return "Coupang"
        domain_part = url.split("/")[2] if "//" in url else url
        return domain_part.replace("www.", "")
