from __future__ import annotations

import random
from typing import Optional

DEMO_DATA: dict[str, list[dict]] = {
    "847130": [  # laptops
        {"origin": "US", "marketplace": "BestBuy", "price_original": 999, "currency": "USD", "duty_pct": 0, "vat_pct": 12, "freight_pct": 25},
        {"origin": "CN", "marketplace": "AliExpress", "price_original": 4899, "currency": "CNY", "duty_pct": 0, "vat_pct": 12, "freight_pct": 25},
        {"origin": "DE", "marketplace": "Amazon DE", "price_original": 1099, "currency": "EUR", "duty_pct": 0, "vat_pct": 12, "freight_pct": 22},
        {"origin": "TR", "marketplace": "Trendyol", "price_original": 32100, "currency": "TRY", "duty_pct": 0, "vat_pct": 12, "freight_pct": 10},
        {"origin": "AE", "marketplace": "Amazon AE", "price_original": 3899, "currency": "AED", "duty_pct": 0, "vat_pct": 12, "freight_pct": 18},
        {"origin": "KR", "marketplace": "Coupang", "price_original": 1320000, "currency": "KRW", "duty_pct": 0, "vat_pct": 12, "freight_pct": 20},
    ],
    "847": [  # general computing
        {"origin": "US", "marketplace": "BestBuy", "price_original": 799, "currency": "USD", "duty_pct": 0, "vat_pct": 12, "freight_pct": 25},
        {"origin": "CN", "marketplace": "AliExpress", "price_original": 3500, "currency": "CNY", "duty_pct": 5, "vat_pct": 12, "freight_pct": 25},
        {"origin": "DE", "marketplace": "Amazon DE", "price_original": 899, "currency": "EUR", "duty_pct": 0, "vat_pct": 12, "freight_pct": 22},
        {"origin": "TR", "marketplace": "Trendyol", "price_original": 28500, "currency": "TRY", "duty_pct": 0, "vat_pct": 12, "freight_pct": 10},
        {"origin": "AE", "marketplace": "Amazon AE", "price_original": 3299, "currency": "AED", "duty_pct": 0, "vat_pct": 12, "freight_pct": 18},
        {"origin": "KR", "marketplace": "Coupang", "price_original": 1100000, "currency": "KRW", "duty_pct": 0, "vat_pct": 12, "freight_pct": 20},
    ],
    "6109": [  # cotton t-shirts
        {"origin": "TR", "marketplace": "Trendyol", "price_original": 189, "currency": "TRY", "duty_pct": 0, "vat_pct": 12, "freight_pct": 10},
        {"origin": "CN", "marketplace": "AliExpress", "price_original": 25, "currency": "CNY", "duty_pct": 12, "vat_pct": 12, "freight_pct": 25},
        {"origin": "IN", "marketplace": "Flipkart", "price_original": 499, "currency": "INR", "duty_pct": 9.5, "vat_pct": 12, "freight_pct": 20},
        {"origin": "BD", "marketplace": "Daraz", "price_original": 350, "currency": "BDT", "duty_pct": 0, "vat_pct": 12, "freight_pct": 15},
    ],
    "61": [  # apparel general
        {"origin": "TR", "marketplace": "Trendyol", "price_original": 250, "currency": "TRY", "duty_pct": 0, "vat_pct": 12, "freight_pct": 10},
        {"origin": "CN", "marketplace": "AliExpress", "price_original": 30, "currency": "CNY", "duty_pct": 12, "vat_pct": 12, "freight_pct": 25},
        {"origin": "IN", "marketplace": "Flipkart", "price_original": 599, "currency": "INR", "duty_pct": 9.5, "vat_pct": 12, "freight_pct": 20},
    ],
    "8703": [  # cars / vehicles
        {"origin": "CN", "marketplace": "Alibaba", "price_original": 85000, "currency": "CNY", "duty_pct": 15, "vat_pct": 12, "freight_pct": 8},
        {"origin": "DE", "marketplace": "Mobile.de", "price_original": 18000, "currency": "EUR", "duty_pct": 15, "vat_pct": 12, "freight_pct": 5},
        {"origin": "KR", "marketplace": "Encar", "price_original": 20000000, "currency": "KRW", "duty_pct": 15, "vat_pct": 12, "freight_pct": 8},
        {"origin": "US", "marketplace": "Cars.com", "price_original": 15000, "currency": "USD", "duty_pct": 15, "vat_pct": 12, "freight_pct": 10},
    ],
    "3004": [  # pharmaceuticals
        {"origin": "IN", "marketplace": "PharmEasy", "price_original": 1500, "currency": "INR", "duty_pct": 5, "vat_pct": 12, "freight_pct": 15},
        {"origin": "CN", "marketplace": "Alibaba", "price_original": 80, "currency": "CNY", "duty_pct": 5, "vat_pct": 12, "freight_pct": 25},
        {"origin": "DE", "marketplace": "DocMorris", "price_original": 45, "currency": "EUR", "duty_pct": 0, "vat_pct": 12, "freight_pct": 20},
    ],
}


def _match_hs(hs_code: str | None) -> str | None:
    if not hs_code:
        return None
    for code in sorted(DEMO_DATA.keys(), key=len, reverse=True):
        if hs_code.startswith(code):
            return code
    return None


def load_demo_data(hs_code: str | None, product_query: str, max_origins: int) -> list[dict]:
    matched = _match_hs(hs_code)
    results = DEMO_DATA.get(matched, [])

    if not results and "thinkpad" in product_query.lower():
        results = DEMO_DATA.get("847130", [])
    if not results and "t-shirt" in product_query.lower():
        results = DEMO_DATA.get("6109", [])
    if not results and "car" in product_query.lower():
        results = DEMO_DATA.get("8703", [])

    if not results:
        results = DEMO_DATA.get("847", [])

    return results[:max_origins]
