from __future__ import annotations

import time

import httpx

from app.log import get_logger

logger = get_logger("currency")

# Primary FX API (free, no key required)
CURRENCY_API_URL = "https://open.er-api.com/v6/latest/USD"

# Fallback API if the primary is unreachable
FALLBACK_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# Last-resort hardcoded rates used when both APIs are unavailable.
# These are intentionally conservative (overestimate cost in USD so the
# caller sees a slightly higher price rather than an unconverted one).
# Source: approximate market rates as of mid-2026.
FALLBACK_RATES: dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.93,
    "GBP": 0.79,
    "JPY": 157.0,
    "CNY": 7.25,
    "KRW": 1380.0,
    "INR": 83.5,
    "TRY": 34.5,
    "AED": 3.67,
    "BDT": 117.0,
    "AUD": 1.50,
    "CAD": 1.37,
    "CHF": 0.90,
    "SGD": 1.35,
    "MYR": 4.70,
    "THB": 36.5,
    "PHP": 58.0,
    "IDR": 16200.0,
    "VND": 25450.0,
    "NOK": 10.6,
    "SEK": 10.5,
    "DKK": 6.95,
    "PLN": 4.05,
    "CZK": 23.0,
    "HUF": 370.0,
    "ILS": 3.75,
    "SAR": 3.75,
    "QAR": 3.64,
    "OMR": 0.38,
    "KWD": 0.31,
    "BHD": 0.38,
    "MXN": 18.5,
    "BRL": 5.25,
    "ARS": 1440.0,
    "CLP": 950.0,
    "COP": 4100.0,
    "PEN": 3.75,
    "ZAR": 18.5,
    "NGN": 1500.0,
    "KES": 130.0,
    "EGP": 48.5,
    "TWD": 32.5,
    "HKD": 7.82,
    "NZD": 1.63,
}

_rates_cache: dict[str, float] = {}
_last_fetch: float | None = None
_CACHE_TTL_SECONDS = 21600  # 6 hours


def _fetch_rates_from_url(url: str) -> dict[str, float] | None:
    """Try to fetch exchange rates from *url*.

    Returns a dict of ``{currency_code: rate}`` if successful, or ``None``
    if the request failed or returned an unexpected payload.
    """
    try:
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("FX API %s returned HTTP %s", url, exc.response.status_code)
        return None
    except httpx.TimeoutException:
        logger.warning("FX API %s timed out", url)
        return None
    except Exception as exc:
        logger.warning("Failed to fetch FX rates from %s: %s", url, exc)
        return None

    # open.er-api.com v6 format: {"result": "success", "rates": {...}}
    if data.get("result") == "success" and "rates" in data:
        return {k: float(v) for k, v in data["rates"].items()}

    # exchangerate-api.com v4 format: {"base": "USD", "rates": {...}}
    if "rates" in data and "base" in data:
        return {k: float(v) for k, v in data["rates"].items()}

    logger.warning("FX API %s returned unrecognised payload format", url)
    return None


def _get_rates() -> dict[str, float]:
    global _rates_cache, _last_fetch
    now = time.time()

    # Return cached rates if they are still fresh
    if _last_fetch is not None and now - _last_fetch < _CACHE_TTL_SECONDS:
        return _rates_cache

    # Try the primary API first
    rates = _fetch_rates_from_url(CURRENCY_API_URL)
    if rates is not None:
        _rates_cache = rates
        _last_fetch = now
        logger.info("FX rates refreshed (%d currencies) from %s", len(rates), CURRENCY_API_URL)
        return _rates_cache

    # If primary failed, try the fallback API
    logger.warning("Primary FX API unavailable, trying fallback ...")
    rates = _fetch_rates_from_url(FALLBACK_API_URL)
    if rates is not None:
        _rates_cache = rates
        _last_fetch = now
        logger.info("FX rates refreshed (%d currencies) from fallback %s", len(rates), FALLBACK_API_URL)
        return _rates_cache

    # If both APIs failed, use hardcoded fallback rates
    logger.warning(
        "Both primary and fallback FX APIs are unreachable — "
        "using hardcoded fallback rates. Amounts may be slightly inaccurate."
    )
    _rates_cache = dict(FALLBACK_RATES)
    _last_fetch = now
    return _rates_cache


def convert_to_usd(amount: float, from_currency: str) -> float:
    """Convert *amount* from *from_currency* to USD.

    Uses a TTL-cached set of exchange rates fetched from a free API.
    If the API is unavailable it falls back to hardcoded rates.
    """
    if from_currency.upper() == "USD":
        return amount

    rates = _get_rates()
    rate = rates.get(from_currency.upper())
    if rate is None:
        logger.warning(
            "No FX rate for %s — returning original amount %.2f unconverted",
            from_currency,
            amount,
        )
        return amount

    return round(amount / rate, 2)
