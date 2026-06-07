from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LandedCostResult:
    price_usd: float
    duty_amount: float
    vat_amount: float
    freight_amount: float
    total_landed: float
    effective_rate_pct: float


def calculate_landed_cost(
    price_usd: float,
    duty_pct: float,
    vat_pct: float,
    freight_pct: float,
) -> LandedCostResult:
    duty = price_usd * duty_pct / 100.0
    vat = price_usd * vat_pct / 100.0
    freight = price_usd * freight_pct / 100.0
    total = price_usd + duty + vat + freight
    effective = ((total - price_usd) / price_usd) * 100.0 if price_usd > 0 else 0.0

    return LandedCostResult(
        price_usd=round(price_usd, 2),
        duty_amount=round(duty, 2),
        vat_amount=round(vat, 2),
        freight_amount=round(freight, 2),
        total_landed=round(total, 2),
        effective_rate_pct=round(effective, 2),
    )
