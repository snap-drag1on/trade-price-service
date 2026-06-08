from __future__ import annotations

import asyncio
import ssl
from dataclasses import dataclass, field
from typing import Any

from app.currency import convert_to_usd
from app.landed_cost import calculate_landed_cost
from app.log import get_logger
from app.scrapers import ApifyAliExpressScraper, RakutenScraper, EbayBrowseApiScraper
from app.supabase_client import get_supabase, get_service_client

logger = get_logger("agent.tools")

# Fix DDGS SSL issue on macOS Python 3.9 (TLSv1_3 not supported)
try:
    import ddgs.http_client2 as _ddgs_hc
    def _patched_ssl_context(verify=True):
        ctx = ssl.create_default_context()
        if verify:
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        return ctx
    _ddgs_hc._get_random_ssl_context = _patched_ssl_context
except Exception:
    pass

apify = ApifyAliExpressScraper()
rakuten = RakutenScraper()
ebay = EbayBrowseApiScraper()


@dataclass
class ToolResult:
    success: bool = True
    data: Any = None
    error: str = ""


COUNTRY_MARKETPLACES: dict[str, dict[str, Any]] = {
    "CN": {"name": "China", "marketplaces": ["1688.com", "alibaba.com", "made-in-china.com", "taobao.com", "tmall.com"]},
    "JP": {"name": "Japan", "marketplaces": ["rakuten.co.jp", "amazon.co.jp", "yahoo.co.jp", "mercari.com"]},
    "KR": {"name": "South Korea", "marketplaces": ["coupang.com", "gmarket.co.kr", "auction.co.kr", "11st.co.kr"]},
    "TW": {"name": "Taiwan", "marketplaces": ["shopee.tw", "ruten.com.tw", "pchome.com.tw", "momoshop.com.tw"]},
    "HK": {"name": "Hong Kong", "marketplaces": ["price.com.hk", "hktvmall.com", "carousell.com.hk"]},
    "SG": {"name": "Singapore", "marketplaces": ["shopee.sg", "amazon.sg", "lazada.sg", "qoo10.sg", "carousell.com.sg"]},
    "MY": {"name": "Malaysia", "marketplaces": ["shopee.com.my", "lazada.com.my", "mudah.my", "pgmall.my"]},
    "TH": {"name": "Thailand", "marketplaces": ["shopee.co.th", "lazada.co.th", "jd.co.th", "central.co.th"]},
    "VN": {"name": "Vietnam", "marketplaces": ["shopee.vn", "lazada.vn", "tiki.vn", "sendo.vn", "thegioididong.com"]},
    "ID": {"name": "Indonesia", "marketplaces": ["tokopedia.com", "shopee.co.id", "bukalapak.com", "lazada.co.id", "blibli.com"]},
    "PH": {"name": "Philippines", "marketplaces": ["shopee.ph", "lazada.com.ph", "zalora.com.ph"]},
    "IN": {"name": "India", "marketplaces": ["amazon.in", "flipkart.com", "meesho.com", "snapdeal.com", "indiamart.com"]},
    "PK": {"name": "Pakistan", "marketplaces": ["daraz.pk", "shophive.com", "homeshopping.pk", "priceoye.pk"]},
    "BD": {"name": "Bangladesh", "marketplaces": ["daraz.com.bd", "ajkerdeal.com", "chaldal.com", "priyoshop.com"]},
    "KZ": {"name": "Kazakhstan", "marketplaces": ["kaspi.kz", "shop.kz", "wildberries.kz", "ozon.kz"]},
    "KG": {"name": "Kyrgyzstan", "marketplaces": ["sulpak.kg", "kiviyo.kg", "wildberries.kg", "ozon.kg"]},
    "TJ": {"name": "Tajikistan", "marketplaces": ["somon.tj", "elita.tj", "bozor.tj"]},
    "TM": {"name": "Turkmenistan", "marketplaces": ["gulstan.tm", "elektron.tm", "bazar.tm"]},
    "TR": {"name": "Turkey", "marketplaces": ["hepsiburada.com", "trendyol.com", "n11.com", "ciceksepeti.com", "amazon.com.tr"]},
    "AE": {"name": "UAE", "marketplaces": ["amazon.ae", "noon.com", "dubizzle.com", "carrefouruae.com"]},
    "SA": {"name": "Saudi Arabia", "marketplaces": ["noon.com", "amazon.sa", "jarir.com", "extra.com"]},
    "IR": {"name": "Iran", "marketplaces": ["digikala.com", "torob.com", "emalls.ir", "zoomg.ir", "bamilo.com"]},
    "IL": {"name": "Israel", "marketplaces": ["zap.co.il", "ksp.co.il", "shufersal.co.il"]},
    "QA": {"name": "Qatar", "marketplaces": ["noon.com", "carrefourqatar.com", "luluqatar.com"]},
    "KW": {"name": "Kuwait", "marketplaces": ["talabat.com", "xcite.com", "jarir.com"]},
    "IQ": {"name": "Iraq", "marketplaces": ["trendyol.com", "hepsiburada.com"]},
    "JO": {"name": "Jordan", "marketplaces": ["amazon.sa", "noon.com", "trendyol.com"]},
    "AZ": {"name": "Azerbaijan", "marketplaces": ["tap.az", "trendyol.com", "hepsiburada.com"]},
    "GE": {"name": "Georgia", "marketplaces": ["trendyol.com", "hepsiburada.com", "amazon.de"]},
    "AM": {"name": "Armenia", "marketplaces": ["trendyol.com", "hepsiburada.com", "amazon.de"]},
}

COUNTRY_TRADE_RULES: dict[str, dict[str, Any]] = {
    "CN": {"name": "China", "currency": "CNY", "export_docs": ["Commercial Invoice", "Packing List", "Bill of Lading/AWB", "Certificate of Origin"], "restricted_categories": ["Dual-use goods", "Electronics with encryption", "Chemicals"], "note": "FOB price includes local logistics to port."},
    "TR": {"name": "Turkey", "currency": "TRY", "agreement": "UZ-TR PTA — reduced duties", "export_docs": ["Commercial Invoice", "Packing List", "EUR.1 or A.TR Certificate", "Certificate of Origin"], "restricted_categories": ["Textiles (quota)", "Steel", "Used goods"], "note": "Check agreement_tariffs for preferential rates."},
    "KR": {"name": "South Korea", "currency": "KRW", "export_docs": ["Commercial Invoice", "Packing List", "Bill of Lading/AWB", "Certificate of Origin"], "restricted_categories": ["Electronics (KCs)", "Cosmetics", "Food"], "note": "MFN rates. No FTA."},
    "IN": {"name": "India", "currency": "INR", "export_docs": ["Commercial Invoice", "Packing List", "Bill of Lading/AWB", "Certificate of Origin", "Phytosanitary"], "restricted_categories": ["Pharmaceuticals (WHO GMP)", "Food (FSSAI)", "Chemicals"], "note": "Pharmaceuticals and textiles are key categories."},
    "AE": {"name": "UAE", "currency": "AED", "export_docs": ["Commercial Invoice", "Packing List", "Certificate of Origin", "Bill of Lading/AWB"], "restricted_categories": ["Gold/jewelry", "Electronics (ESMA)", "Used goods"], "note": "Re-export hub for CN/IN/TR goods."},
    "KZ": {"name": "Kazakhstan", "currency": "KZT", "agreement": "CIS-FTA — 0% duty", "export_docs": ["Commercial Invoice", "Packing List", "CT-1 Certificate", "Bill of Lading/AWB"], "restricted_categories": ["Alcohol", "Tobacco", "Weapons"], "note": "Easiest corridor for UZ. Shared border."},
    "JP": {"name": "Japan", "currency": "JPY", "export_docs": ["Commercial Invoice", "Packing List", "Air Waybill", "Certificate of Origin"], "restricted_categories": ["Used vehicles (age)", "Electronics (PSE)", "Food"], "note": "Used cars popular for UZ."},
    "SG": {"name": "Singapore", "currency": "SGD", "export_docs": ["Commercial Invoice", "Packing List", "Certificate of Origin", "Bill of Lading/AWB"], "restricted_categories": ["Chewing gum", "Fireworks", "Weapons"], "note": "Major transshipment hub."},
    "MY": {"name": "Malaysia", "currency": "MYR", "export_docs": ["Commercial Invoice", "Packing List", "Certificate of Origin", "Bill of Lading/AWB", "Phytosanitary"], "restricted_categories": ["Palm oil (quota)", "Electronics (SIRIM)", "Wood"], "note": "Palm oil, electronics, rubber."},
}


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Real-time product search from a given origin country. Uses AliExpress (CN), Rakuten (JP), or eBay (US/DE/GB) APIs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "enum": ["CN", "JP", "US", "DE", "GB", "FR", "IT", "ES", "AU", "CA"],
                        "description": "Origin country code",
                    },
                    "query": {"type": "string", "description": "Product search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum products to return",
                        "default": 3,
                    },
                },
                "required": ["origin", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the current exchange rate from a currency to USD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "enum": ["CNY", "JPY", "EUR", "GBP", "USD", "KRW", "TRY", "AED", "INR", "RUB"],
                        "description": "Currency code to convert to USD",
                    }
                },
                "required": ["currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trade_costs",
            "description": "Get trade costs (duty %, VAT %, freight %) between origin and destination for a given HS code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin country code (2 letters)"},
                    "destination": {
                        "type": "string",
                        "description": "Destination country code (2 letters)",
                    },
                    "hs_code": {"type": "string", "description": "HS code (6 digits)"},
                    "transport_mode": {
                        "type": "string",
                        "enum": ["rail", "air", "sea", "road"],
                        "default": "rail",
                    },
                },
                "required": ["origin", "destination", "hs_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_landed_cost",
            "description": "Calculate total landed cost including duty, VAT, and freight.",
            "parameters": {
                "type": "object",
                "properties": {
                    "price": {"type": "number", "description": "Product price in original currency"},
                    "currency": {"type": "string", "description": "Currency code (ISO 4217)"},
                    "duty_pct": {"type": "number", "description": "Import duty percentage"},
                    "vat_pct": {"type": "number", "description": "VAT percentage"},
                    "freight_pct": {"type": "number", "description": "Freight percentage"},
                },
                "required": ["price", "currency", "duty_pct", "vat_pct", "freight_pct"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_freight_corridor",
            "description": "Get freight details (distance km, transit days, rate) between origin and destination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin country code"},
                    "destination": {"type": "string", "description": "Destination country code"},
                    "transport_mode": {
                        "type": "string",
                        "enum": ["rail", "air", "sea", "road"],
                        "default": "rail",
                    },
                },
                "required": ["origin", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_uzum",
            "description": "Search Uzum Market (uzum.uz) for real product prices in Uzbekistan in UZS sums. If error, fallback to web_search with 'site:uzum.uz' prefix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Product search query in Uzbek or Russian"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for product prices, specifications, or any real-time information. Best for finding Alibaba/Aliexpress/eBay prices and any current market data. Example: 'alibaba LED lamp 8539 price USD' or 'site:ebay.com power bank 8507'",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Detailed search query. Use 'alibaba' or 'site:alibaba.com' prefix for Chinese wholesale prices."},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_opportunities",
            "description": "Discover trending product opportunities for Uzbekistan import. Searches web trends, Telegram discussions, and checks Uzum marketplace competition. Returns products with high demand and low competition scores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum opportunities to return",
                        "default": 5,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_cn_sources",
            "description": "Search Chinese wholesale sources (1688.com, Alibaba, Made-in-China) for product prices. Falls back to web search with site:alibaba.com prefix when APIs are unavailable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Product search query in English or Chinese"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_uz_marketplaces",
            "description": "Search all major Uzbekistan marketplaces (Uzum, Olcha, Asaxiy, Texnomart, Mediapark) for product prices. Returns combined results from all sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Product search query in Uzbek or Russian"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return per marketplace",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_logistics_multi_route",
            "description": "Compare logistics routes (air, rail, road, sea) between origin and destination. Returns transit days and cost per kg for each transport mode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin country code (2 letters, e.g. CN, US, TR)"},
                    "destination": {"type": "string", "description": "Destination country code (2 letters, e.g. UZ)"},
                    "weight_kg": {
                        "type": "number",
                        "description": "Package weight in kg for cost calculation",
                        "default": 1,
                    },
                },
                "required": ["origin", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_country_marketplaces",
            "description": "Search marketplaces of a specific Asian country for product prices. Returns results from known marketplaces via web search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "Country code (2 letters, e.g. KR, IN, TR, AE, SG)",
                    },
                    "query": {"type": "string", "description": "Product search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 5,
                    },
                },
                "required": ["country", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_country_trade_rules",
            "description": "Get customs/duty rules, required documents, and restricted categories for a specific origin country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "Country code (2 letters, e.g. CN, TR, KR, IN, AE, KZ)",
                    },
                },
                "required": ["country"],
            },
        },
    },
]


async def search_products(origin: str, query: str, max_results: int = 3) -> ToolResult:
    origin = origin.upper()
    try:
        if origin == "CN":
            return await search_cn_sources(query, max_results)
        elif origin == "JP" and rakuten.is_configured:
            results = await asyncio.wait_for(rakuten.search(query, max_results), timeout=12)
        elif origin in ("US", "DE", "GB") and ebay.is_configured:
            results = await asyncio.wait_for(ebay.search(query, origin), timeout=12)
        else:
            return await search_cn_sources(query, max_results)
        output = [
            {
                "price": r.price,
                "currency": r.currency,
                "product_name": r.product_name,
                "marketplace": r.marketplace,
                "confidence": r.confidence,
                "source_url": r.source_url,
            }
            for r in results
        ]
        return ToolResult(data=output)
    except Exception as exc:
        logger.warning("search_products(%s, %s) failed: %s", origin, query, exc)
        return await search_cn_sources(query, max_results)


async def get_exchange_rate(currency: str) -> ToolResult:
    try:
        usd_amount = convert_to_usd(1.0, currency.upper())
        return ToolResult(data={"from": currency.upper(), "to": "USD", "rate": usd_amount})
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


async def get_trade_costs(
    origin: str,
    destination: str,
    hs_code: str,
    transport_mode: str = "rail",
) -> ToolResult:
    supabase = get_service_client()
    if supabase is None:
        supabase = get_supabase()
    if supabase is None:
        return ToolResult(success=False, error="Supabase not available")
    try:
        data = supabase.rpc(
            "api_search_sourcing",
            {
                "cif_value": 100,
                "destination": destination.upper(),
                "hs_code": hs_code,
                "product_query": "",
                "transport_mode": transport_mode,
            },
        ).execute()
        results = data.data.get("results", []) if isinstance(data.data, dict) else []
        for entry in results:
            if isinstance(entry, dict) and entry.get("origin", "").upper() == origin.upper():
                tc = entry.get("trade_costs", {})
                return ToolResult(
                    data={
                        "origin": origin.upper(),
                        "destination": destination.upper(),
                        "hs_code": hs_code,
                        "duty_pct": float(tc.get("duty_rate_pct", 0)),
                        "vat_pct": float(tc.get("vat_rate_pct", 0)),
                        "freight_pct": float(tc.get("freight_rate_pct", 15)),
                    }
                )
        return ToolResult(
            success=False,
            error=f"No trade costs found for {origin} → {destination} HS {hs_code}",
        )
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


async def calculate_landed(
    price: float,
    currency: str,
    duty_pct: float,
    vat_pct: float,
    freight_pct: float,
) -> ToolResult:
    try:
        price_usd = convert_to_usd(price, currency)
        lc = calculate_landed_cost(price_usd, duty_pct, vat_pct, freight_pct)
        return ToolResult(
            data={
                "price_original": price,
                "currency": currency.upper(),
                "price_usd": lc.price_usd,
                "duty_amount": lc.duty_amount,
                "vat_amount": lc.vat_amount,
                "freight_amount": lc.freight_amount,
                "total_landed": lc.total_landed,
                "effective_rate_pct": lc.effective_rate_pct,
            }
        )
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


async def get_freight_corridor(origin: str, destination: str, transport_mode: str = "rail") -> ToolResult:
    supabase = get_service_client()
    if supabase is None:
        supabase = get_supabase()
    if supabase is None:
        return ToolResult(success=False, error="Supabase not available")
    try:
        data = supabase.table("freight_corridors") \
            .select("*") \
            .eq("origin_country_code", origin.upper()) \
            .eq("destination_country_code", destination.upper()) \
            .eq("transport_mode", transport_mode) \
            .execute()
        if data.data and len(data.data) > 0:
            row = data.data[0]
            return ToolResult(
                data={
                    "origin": row.get("origin_country_code"),
                    "destination": row.get("destination_country_code"),
                    "transport_mode": row.get("transport_mode"),
                    "transit_days_min": int(row.get("transit_days_min", 0)),
                    "transit_days_max": int(row.get("transit_days_max", 0)),
                    "cost_per_kg_usd": float(row.get("cost_per_kg_usd") or 0),
                    "cost_per_container_usd": float(row.get("cost_per_container_usd") or 0),
                    "cost_per_cbm_usd": float(row.get("cost_per_cbm_usd") or 0),
                }
            )
        return ToolResult(success=False, error=f"No freight corridor found for {origin} → {destination} by {transport_mode}")
    except Exception as exc:
        return ToolResult(success=False, error=str(exc))


async def search_uzum(query: str, max_results: int = 5) -> ToolResult:
    import httpx
    from datetime import datetime, timezone, timedelta

    # === 24h CACHE CHECK: marketplace_listings ===
    try:
        supabase = get_service_client()
        if supabase:
            cache_hit = supabase.table("marketplace_listings") \
                .select("product_catalog!inner(product_name,brand,model),last_price,currency,url,last_checked") \
                .eq("marketplace", "uzum") \
                .ilike("listing_title", f"%{query}%") \
                .execute()
            rows = cache_hit.data or []
            fresh = []
            for r in rows:
                lc = r.get("last_checked")
                lp = r.get("last_price")
                if lc and lp is not None:
                    age = datetime.now(timezone.utc) - datetime.fromisoformat(lc.replace("Z", "+00:00"))
                    if age < timedelta(hours=24):
                        fresh.append({
                            "product_name": r.get("product_catalog", {}).get("product_name", r.get("listing_title", "")),
                            "price_uzs": float(lp),
                            "price_usd": round(float(lp) / 12700, 2),
                            "currency": r.get("currency", "UZS"),
                            "marketplace": "Uzum",
                            "source_url": r.get("url", ""),
                            "cached": True,
                        })
            if fresh:
                logger.info("Uzum cache HIT for '%s': %d results", query, len(fresh))
                return ToolResult(data=fresh[:max_results])
            logger.info("Uzum cache MISS for '%s'", query)
    except Exception as exc:
        logger.debug("Uzum cache check failed: %s", exc)

    # === LIVE LOOKUP ===

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TradePriceBot/1.0)",
        "Accept": "application/json",
        "Accept-Language": "uz-UZ",
    }

    # Try new API (umarket.uz — may require auth token)
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api.umarket.uz/api/v2/product/search",
                params={"query": query, "page": 1, "size": max_results},
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", {}).get("items", data.get("payload", []))
                results = []
                for item in items[:max_results]:
                    results.append({
                        "product_name": item.get("title", item.get("name", "")),
                        "price_uzs": float(item.get("price", item.get("priceUzs", 0))),
                        "price_usd": round(float(item.get("price", item.get("priceUzs", 0))) / 12700, 2),
                        "currency": "UZS",
                        "marketplace": "Uzum",
                        "source_url": f"https://uzum.uz/product/{item.get('id', '')}",
                    })
                return ToolResult(data=results)
    except Exception as exc:
        logger.debug("Uzum new API failed: %s", exc)

    # Try old API (deprecated — may still work on newer Python)
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api.uzum.uz/api/search/v2/search",
                params={"query": query, "page": 1, "size": max_results},
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", {}).get("items", [])
                results = []
                for item in items[:max_results]:
                    results.append({
                        "product_name": item.get("title", ""),
                        "price_uzs": float(item.get("price", 0)),
                        "price_usd": round(float(item.get("price", 0)) / 12700, 2),
                        "currency": "UZS",
                        "marketplace": "Uzum",
                        "source_url": f"https://uzum.uz/product/{item.get('id', '')}",
                    })
                return ToolResult(data=results)
    except Exception as exc:
        logger.debug("Uzum old API failed: %s", exc)

    # Fallback: DDGS web search
    try:
        from ddgs import DDGS
        loop = asyncio.get_event_loop()
        web_results = await loop.run_in_executor(
            None,
            lambda: [
                {"title": r.get("title", ""), "href": r.get("href", ""), "body": r.get("body", "")}
                for r in DDGS().text(f"site:uzum.uz {query}", max_results=max_results)
            ],
        )
        if web_results:
            return ToolResult(data=web_results)
    except Exception as exc:
        logger.debug("Uzum web search fallback failed: %s", exc)

    return ToolResult(success=False, error="Uzum API unreachable — no prices available")


async def web_search(query: str, max_results: int = 5) -> ToolResult:
    try:
        from ddgs import DDGS
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: [
                {"title": r.get("title", ""), "href": r.get("href", ""), "body": r.get("body", "")}
                for r in DDGS().text(query, max_results=max_results)
            ],
        )
        return ToolResult(data=results)
    except ImportError:
        return ToolResult(success=False, error="ddgs not installed")
    except Exception as exc:
        logger.warning("Web search failed for '%s': %s", query, exc)
        return ToolResult(success=False, error=f"Web search error: {exc}")


async def discover_opportunities(max_results: int = 5) -> ToolResult:
    """Discover product opportunities using DB signals + web trends."""
    results = []
    sources_used = []

    # 1. Check DB for existing opportunity signals
    try:
        supabase = get_service_client()
        if supabase:
            cached = supabase.table("opportunity_signals") \
                .select("*") \
                .order("demand_score", desc=True) \
                .limit(max_results) \
                .execute()
            rows = cached.data or []
            for r in rows:
                results.append({
                    "product_name": r.get("product_name"),
                    "category": r.get("category"),
                    "demand_score": r.get("demand_score"),
                    "competition_score": r.get("competition_score"),
                    "signal": r.get("signal_text"),
                    "confidence": r.get("confidence"),
                    "source": "DB",
                })
            if results:
                sources_used.append("opportunity_signals table")
    except Exception as exc:
        logger.debug("DB opportunity check failed: %s", exc)

    # 2. Web search for trending products in Uzbekistan
    try:
        from ddgs import DDGS
        loop = asyncio.get_event_loop()
        web_results = await loop.run_in_executor(
            None,
            lambda: [
                {"title": r.get("title", ""), "href": r.get("href", ""), "body": r.get("body", "")}
                for r in DDGS().text("O'zbekistonda import qilinadigan eng kerakli mahsulotlar 2025", max_results=3)
            ],
        )
        if web_results:
            sources_used.append("web search trends")
            for wr in web_results:
                title = wr.get("title", "")
                body = wr.get("body", "")
                if any(kw in title.lower() or kw in body.lower() for kw in ["import", "mahsulot", "biznes", "sotish", "kerak"]):
                    results.append({
                        "product_name": title[:100],
                        "category": "Noma'lum",
                        "demand_score": 50,
                        "competition_score": 50,
                        "signal": body[:200] if body else title[:200],
                        "confidence": 0.4,
                        "source": "Web",
                    })
    except Exception as exc:
        logger.debug("Web trend search failed: %s", exc)

    return ToolResult(data={
        "opportunities": results[:max_results],
        "sources": sources_used,
    })


async def search_cn_sources(query: str, max_results: int = 5) -> ToolResult:
    """Search Chinese wholesale sources: 1688.com, Alibaba, Made-in-China."""
    combined = []
    
    # Try web_search for each source
    sources = [
        {"name": "Alibaba", "prefix": "site:alibaba.com"},
        {"name": "1688", "prefix": "site:1688.com"},
        {"name": "Made-in-China", "prefix": "site:made-in-china.com"},
    ]

    for source in sources:
        try:
            result = await web_search(f"{source['prefix']} {query}", max_results=2)
            if result.success and result.data:
                for item in result.data[:2]:
                    combined.append({
                        "source": source["name"],
                        "title": item.get("title", ""),
                        "url": item.get("href", ""),
                        "snippet": item.get("body", ""),
                    })
        except Exception as exc:
            logger.debug("CN source %s failed: %s", source["name"], exc)

    if not combined:
        # Try one more generic search
        try:
            result = await web_search(f"alibaba {query} price USD wholesale", max_results=3)
            if result.success and result.data:
                for item in result.data[:3]:
                    combined.append({
                        "source": "Alibaba (generic)",
                        "title": item.get("title", ""),
                        "url": item.get("href", ""),
                        "snippet": item.get("body", ""),
                    })
        except Exception as exc:
            logger.debug("Generic CN search failed: %s", exc)

    if not combined:
        return ToolResult(success=False, error=f"No Chinese wholesale prices found for '{query}'")

    return ToolResult(data=combined)


async def search_uz_marketplaces(query: str, max_results: int = 3) -> ToolResult:
    """Search all Uzbekistan marketplaces for product prices."""
    combined = []

    # 1. Try Uzum first
    try:
        uzum_result = await search_uzum(query, max_results=max_results)
        if uzum_result.success and uzum_result.data:
            for item in uzum_result.data[:max_results]:
                combined.append({
                    **item,
                    "marketplace": "Uzum",
                })
    except Exception as exc:
        logger.debug("Uzum search failed: %s", exc)

    # 2. Try Olcha
    try:
        olcha = await web_search(f"site:olcha.uz {query}", max_results=2)
        if olcha.success and olcha.data:
            for item in olcha.data[:2]:
                combined.append({
                    "product_name": item.get("title", ""),
                    "price_uzs": 0,
                    "price_usd": 0,
                    "currency": "UZS",
                    "marketplace": "Olcha",
                    "source_url": item.get("href", ""),
                })
    except Exception as exc:
        logger.debug("Olcha search failed: %s", exc)

    # 3. Try Asaxiy
    try:
        asaxiy = await web_search(f"site:asaxiy.uz {query}", max_results=2)
        if asaxiy.success and asaxiy.data:
            for item in asaxiy.data[:2]:
                combined.append({
                    "product_name": item.get("title", ""),
                    "price_uzs": 0,
                    "price_usd": 0,
                    "currency": "UZS",
                    "marketplace": "Asaxiy",
                    "source_url": item.get("href", ""),
                })
    except Exception as exc:
        logger.debug("Asaxiy search failed: %s", exc)

    # 4. Try Texnomart
    try:
        texno = await web_search(f"site:texnomart.uz {query}", max_results=2)
        if texno.success and texno.data:
            for item in texno.data[:2]:
                combined.append({
                    "product_name": item.get("title", ""),
                    "price_uzs": 0,
                    "price_usd": 0,
                    "currency": "UZS",
                    "marketplace": "Texnomart",
                    "source_url": item.get("href", ""),
                })
    except Exception as exc:
        logger.debug("Texnomart search failed: %s", exc)

    # 5. Try Mediapark
    try:
        media = await web_search(f"site:mediapark.uz {query}", max_results=2)
        if media.success and media.data:
            for item in media.data[:2]:
                combined.append({
                    "product_name": item.get("title", ""),
                    "price_uzs": 0,
                    "price_usd": 0,
                    "currency": "UZS",
                    "marketplace": "Mediapark",
                    "source_url": item.get("href", ""),
                })
    except Exception as exc:
        logger.debug("Mediapark search failed: %s", exc)

    if not combined:
        return ToolResult(success=False, error=f"No Uzbekistan marketplace prices found for '{query}'")

    return ToolResult(data=combined)


async def get_logistics_multi_route(origin: str, destination: str, weight_kg: float = 1) -> ToolResult:
    """Compare logistics routes (air, rail, road) between origin and destination."""
    modes = ["air", "rail", "road"]
    routes = []

    supabase = get_service_client()
    if supabase is None:
        supabase = get_supabase()
    if supabase is None:
        return ToolResult(data={
            "routes": [],
            "note": "Supabase unavailable — using estimated values",
            "estimated": True,
        })

    for mode in modes:
        try:
            data = supabase.table("freight_corridors") \
                .select("*") \
                .eq("origin_country_code", origin.upper()) \
                .eq("destination_country_code", destination.upper()) \
                .eq("transport_mode", mode) \
                .execute()
            if data.data and len(data.data) > 0:
                row = data.data[0]
                cost_per_kg = float(row.get("cost_per_kg_usd") or 0)
                routes.append({
                    "transport_mode": row.get("transport_mode"),
                    "transit_days_min": int(row.get("transit_days_min", 0)),
                    "transit_days_max": int(row.get("transit_days_max", 0)),
                    "cost_per_kg_usd": cost_per_kg,
                    "total_cost_usd": round(cost_per_kg * weight_kg, 2) if cost_per_kg > 0 else 0,
                })
        except Exception as exc:
            logger.debug("Freight corridor %s failed: %s", mode, exc)

    if not routes:
        return ToolResult(success=False, error=f"No logistics routes found for {origin} → {destination}")

    return ToolResult(data={
        "origin": origin.upper(),
        "destination": destination.upper(),
        "weight_kg": weight_kg,
        "routes": sorted(routes, key=lambda r: r.get("transit_days_min", 999)),
    })


async def search_country_marketplaces(country: str, query: str, max_results: int = 5) -> ToolResult:
    country = country.upper()
    info = COUNTRY_MARKETPLACES.get(country)
    if not info:
        return ToolResult(success=False, error=f"No marketplaces configured for country '{country}'")
    combined = []
    for marketplace in info["marketplaces"][:4]:
        try:
            result = await web_search(f"site:{marketplace} {query}", max_results=2)
            if result.success and result.data:
                for item in result.data[:2]:
                    combined.append({
                        "product_name": item.get("title", ""),
                        "price": 0,
                        "currency": "USD",
                        "marketplace": marketplace,
                        "source_url": item.get("href", ""),
                        "snippet": item.get("body", ""),
                    })
        except Exception as exc:
            logger.debug("Marketplace %s search failed: %s", marketplace, exc)
    if not combined:
        return ToolResult(success=False, error=f"No marketplace results for '{query}' in {info['name']}")
    return ToolResult(data={"country": country, "country_name": info["name"], "results": combined[:max_results]})


async def get_country_trade_rules(country: str) -> ToolResult:
    country = country.upper()
    info = COUNTRY_TRADE_RULES.get(country)
    if not info:
        return ToolResult(success=False, error=f"No trade rules configured for country '{country}'")
    return ToolResult(data=info)


TOOL_MAP = {
    "search_products": search_products,
    "get_exchange_rate": get_exchange_rate,
    "get_trade_costs": get_trade_costs,
    "calculate_landed_cost": calculate_landed,
    "get_freight_corridor": get_freight_corridor,
    "search_uzum": search_uzum,
    "web_search": web_search,
    "discover_opportunities": discover_opportunities,
    "search_cn_sources": search_cn_sources,
    "search_uz_marketplaces": search_uz_marketplaces,
    "get_logistics_multi_route": get_logistics_multi_route,
    "search_country_marketplaces": search_country_marketplaces,
    "get_country_trade_rules": get_country_trade_rules,
}
