from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cache import compute_query_hash
from app.currency import convert_to_usd
from app.landed_cost import calculate_landed_cost
from app.log import get_logger
from app.supabase_client import get_supabase, get_service_client

logger = get_logger("prices")

router = APIRouter()


class ManualPriceRequest(BaseModel):
    product_query: str = Field(..., min_length=1, description="Product name")
    origin: str = Field(..., min_length=2, max_length=2, description="Origin country code")
    destination: str = Field(..., min_length=2, max_length=2, description="Destination country code")
    price_original: float = Field(..., gt=0, description="Price in original currency (FOB/CIF)")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code (ISO 4217)")
    hs_code: Optional[str] = Field(None, description="HS code (6 digits)")
    transport_mode: str = Field(default="rail", pattern="^(rail|air|sea|road)$")
    source_url: Optional[str] = Field(None, description="Optional URL or note about source")
    marketplace: str = Field(default="Manual", description="Supplier or marketplace name")
    ttl_hours: int = Field(default=168, ge=1, le=8760, description="Cache TTL in hours (default 7 days)")


class ManualPriceResponse(BaseModel):
    query: dict
    price_usd: float
    duty_pct: float
    vat_pct: float
    freight_pct: float
    duty_amount: float
    vat_amount: float
    freight_amount: float
    total_landed: float
    effective_rate_pct: float
    stored: bool


def _fetch_trade_costs_sync(
    origin: str,
    destination: str,
    hs_code: str | None,
    transport_mode: str,
) -> dict:
    supabase = get_supabase()
    if supabase is None:
        return {"duty_pct": 0, "vat_pct": 0, "freight_pct": 15}

    duty_pct = 0.0
    vat_pct = 0.0
    freight_pct = 15.0

    if hs_code and len(hs_code) >= 4:
        try:
            data = supabase.rpc(
                "api_search_sourcing",
                {
                    "hs_code": hs_code,
                    "destination": destination,
                    "product_query": "test",
                    "cif_value": 1000,
                    "transport_mode": transport_mode,
                },
            ).execute()
            results = data.data.get("results", []) if isinstance(data.data, dict) else (data.data if isinstance(data.data, list) else [])
            for entry in results:
                if isinstance(entry, dict) and entry.get("origin", "").upper() == origin.upper():
                    tc = entry.get("trade_costs", {})
                    duty_pct = float(tc.get("duty_rate_pct", duty_pct))
                    vat_pct = float(tc.get("vat_rate_pct", vat_pct))
                    freight_pct = float(tc.get("freight_rate_pct", freight_pct))
                    break
        except Exception as exc:
            logger.warning("Trade costs RPC failed: %s", exc)

    if vat_pct == 0:
        try:
            data = supabase.table("country_taxes").select("tax_rate_pct") \
                .eq("country_code", destination.upper()) \
                .eq("tax_type", "vat") \
                .eq("applies_to", "cif_plus_duty") \
                .execute()
            if data.data and len(data.data) > 0:
                vat_pct = float(data.data[0].get("tax_rate_pct", 0))
        except Exception as exc:
            logger.warning("VAT lookup failed: %s", exc)

    return {
        "duty_pct": duty_pct,
        "vat_pct": vat_pct,
        "freight_pct": freight_pct,
    }


@router.post("/price/manual", response_model=ManualPriceResponse)
async def submit_manual_price(req: ManualPriceRequest) -> ManualPriceResponse:
    trade = _fetch_trade_costs_sync(req.origin, req.destination, req.hs_code, req.transport_mode)

    price_usd = convert_to_usd(req.price_original, req.currency)
    landed = calculate_landed_cost(
        price_usd,
        trade["duty_pct"],
        trade["vat_pct"],
        trade["freight_pct"],
    )

    stored = False
    service = get_service_client()
    if service is not None:
        try:
            query_hash = compute_query_hash(req.product_query, req.hs_code, req.destination)
            now = datetime.now(timezone.utc)
            expires = now + timedelta(hours=req.ttl_hours)
            service.table("price_cached_results").insert({
                "query_hash": query_hash,
                "product_name": f"{req.product_query} (manual)",
                "hs_code": req.hs_code,
                "destination": req.destination.upper(),
                "origin": req.origin.upper(),
                "price_usd": landed.price_usd,
                "price_original": req.price_original,
                "currency": req.currency.upper(),
                "source_url": req.source_url or "",
                "marketplace": req.marketplace,
                "confidence": 0.95,
                "total_landed": landed.total_landed,
                "duty_pct": trade["duty_pct"],
                "vat_pct": trade["vat_pct"],
                "freight_pct": trade["freight_pct"],
                "scraped_at": now.isoformat(),
                "expires_at": expires.isoformat(),
            }).execute()
            stored = True
            logger.info("Manual price stored for '%s' (%s → %s)", req.product_query, req.origin, req.destination)
        except Exception as exc:
            logger.error("Failed to store manual price: %s", exc)

    return ManualPriceResponse(
        query=req.model_dump(),
        price_usd=landed.price_usd,
        duty_pct=trade["duty_pct"],
        vat_pct=trade["vat_pct"],
        freight_pct=trade["freight_pct"],
        duty_amount=landed.duty_amount,
        vat_amount=landed.vat_amount,
        freight_amount=landed.freight_amount,
        total_landed=landed.total_landed,
        effective_rate_pct=landed.effective_rate_pct,
        stored=stored,
    )
