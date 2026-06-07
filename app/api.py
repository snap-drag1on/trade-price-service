from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import uuid
from datetime import datetime

from app.agent.engine import run_agent
from app.agent.models import (
    QueryRequest, QueryResponse,
    PriceCheckRequest, PriceCheckResponse,
    ComparisonRequest, ComparisonResponse,
)
from app.currency import convert_to_usd
from app.landed_cost import calculate_landed_cost
from app.cache import compute_query_hash, check_cache, write_cache
from app.supabase_client import get_service_client, get_supabase
from app.log import get_logger

logger = get_logger("api")
router = APIRouter(prefix="/api/v1", tags=["main"])

TASK_STORE = {}


@router.post("/query", response_model=QueryResponse)
async def create_query(
    req: QueryRequest,
    background_tasks: BackgroundTasks,
) -> QueryResponse:
    task_id = str(uuid.uuid4())

    background_tasks.add_task(
        _process_query_background,
        task_id=task_id,
        product=req.product,
        language=req.language,
        destination=req.destination,
        use_cache=req.use_cache,
    )

    return QueryResponse(
        success=True,
        task_id=task_id,
        status="processing",
        timestamp=datetime.now(),
    )


@router.get("/query/{task_id}", response_model=QueryResponse)
async def get_query_status(task_id: str) -> QueryResponse:
    if task_id not in TASK_STORE:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = TASK_STORE[task_id]

    return QueryResponse(
        success=not task_data.get("error"),
        task_id=task_id,
        status=task_data.get("status", "unknown"),
        phases=task_data.get("phases"),
        result=task_data.get("result"),
        error=task_data.get("error"),
        timestamp=task_data.get("timestamp", datetime.now()),
    )


async def _process_query_background(
    task_id: str,
    product: str,
    language: str,
    destination: str,
    use_cache: bool,
):
    try:
        TASK_STORE[task_id] = {"status": "processing", "timestamp": datetime.now()}

        if use_cache:
            query_hash = compute_query_hash(product, None, destination)
            cached = await check_cache(query_hash)
            if cached:
                TASK_STORE[task_id] = {
                    "status": "completed",
                    "result": {"source": "cache", "data": cached},
                    "timestamp": datetime.now(),
                }
                logger.info("Cache HIT for %s", task_id)
                return

        result = await run_agent(product, max_tool_rounds=10)

        if isinstance(result, str):
            try:
                result = {"answer": result}
            except Exception:
                result = {"answer": result}

        TASK_STORE[task_id] = {
            "status": "completed",
            "result": result,
            "phases": result.get("phases", {}),
            "timestamp": datetime.now(),
        }
        logger.info("Query completed: %s", task_id)

    except Exception as e:
        TASK_STORE[task_id] = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(),
        }
        logger.error("Query failed %s: %s", task_id, e)


@router.post("/price-check", response_model=PriceCheckResponse)
async def check_price(req: PriceCheckRequest) -> PriceCheckResponse:
    try:
        supabase = get_supabase()
        if supabase is None:
            raise HTTPException(status_code=502, detail="Supabase unavailable")

        data = supabase.rpc(
            "api_search_sourcing",
            {
                "hs_code": req.hs_code or "",
                "destination": req.destination,
                "cif_value": 100,
                "transport_mode": req.transport_mode,
                "product_query": req.product_query,
            },
        ).execute()

        results = data.data.get("results", []) if isinstance(data.data, dict) else []

        duty_pct = 0.0
        vat_pct = 0.0
        freight_pct = 15.0

        for entry in results:
            if entry.get("origin", "").upper() == req.origin.upper():
                tc = entry.get("trade_costs", {})
                duty_pct = float(tc.get("duty_rate_pct", 0))
                vat_pct = float(tc.get("vat_rate_pct", 0))
                freight_pct = float(tc.get("freight_rate_pct", 15))
                break

        price_usd = convert_to_usd(req.price_original, req.currency)
        landed = calculate_landed_cost(price_usd, duty_pct, vat_pct, freight_pct)

        uzs_rate = 12700
        total_uzs = landed.total_landed * uzs_rate

        return PriceCheckResponse(
            total_landed_usd=landed.total_landed,
            total_landed_uzs=total_uzs,
            breakdown={
                "product": landed.price_usd,
                "duty": landed.duty_amount,
                "vat": landed.vat_amount,
                "freight": landed.freight_amount,
            },
            saved=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Price check failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=ComparisonResponse)
async def compare_offers(req: ComparisonRequest) -> ComparisonResponse:
    try:
        price_1 = req.offer_1.get("price", 0)
        price_2 = req.offer_2.get("price", 0)

        landed_1 = calculate_landed_cost(price_1, 5, 12, 15)
        landed_2 = calculate_landed_cost(price_2, 5, 12, 15)

        savings_usd = abs(landed_2.total_landed - landed_1.total_landed)
        savings_percent = (
            (savings_usd / landed_2.total_landed * 100)
            if landed_2.total_landed > 0
            else 0
        )

        best = "Offer 1" if landed_1.total_landed < landed_2.total_landed else "Offer 2"

        return ComparisonResponse(
            offer_1_landed=landed_1.total_landed,
            offer_2_landed=landed_2.total_landed,
            savings_usd=savings_usd,
            savings_percent=savings_percent,
            recommendation=f"{best} arzonroq",
        )

    except Exception as e:
        logger.error("Comparison failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "Trade Price Service",
        "timestamp": datetime.now(),
        "tasks_active": len(
            [t for t in TASK_STORE.values() if t.get("status") == "processing"]
        ),
    }


@router.post("/admin/sync-cbu")
async def sync_cbu_rates():
    try:
        supabase = get_service_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Supabase not configured")

        result = supabase.rpc("sync_cbu_exchange_rates").execute()

        return {"success": True, "message": "CBU sync completed", "result": result.data}
    except Exception as e:
        logger.error("CBU sync failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
