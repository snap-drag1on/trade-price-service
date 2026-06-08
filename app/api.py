from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Any
import uuid
import asyncio
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
from app.task_store import save_task, get_task, update_task, count_active_tasks
from app.log import get_logger

logger = get_logger("api")
router = APIRouter(prefix="/api/v1", tags=["main"])

UI_PHASE_MAP = {
    "router": {"label": "router", "order": 0},
    "opportunity": {"label": "bozor_tahlili", "order": 1},
    "market_research": {"label": "narxlar_yigilmoqda", "order": 2},
    "logistics": {"label": "narxlar_yigilmoqda", "order": 2},
    "trade_engine": {"label": "narxlar_yigilmoqda", "order": 2},
    "profit": {"label": "foyda_hisoblanmoqda", "order": 3},
    "decision": {"label": "tavsiya_tayyorlanmoqda", "order": 4},
}


def _progress_callback(task_id: str):
    def callback(phase: str, data: dict):
        ui_label = UI_PHASE_MAP.get(phase, {}).get("label", phase)
        phase_data = {**data, "ui_label": ui_label}
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(update_task(task_id, {"phases": {phase: phase_data}}))
    return callback


@router.post("/query", response_model=QueryResponse)
async def create_query(
    req: QueryRequest,
    background_tasks: BackgroundTasks,
) -> QueryResponse:
    task_id = str(uuid.uuid4())

    await save_task(task_id, {
        "status": "processing",
        "flow": "",
        "phases": {},
    })

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
    task_data = await get_task(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return QueryResponse(
        success=not task_data.get("error"),
        task_id=task_id,
        status=task_data.get("status", "unknown"),
        flow=task_data.get("flow"),
        phases=task_data.get("phases"),
        result=task_data.get("result"),
        error=task_data.get("error"),
        timestamp=datetime.now(),
    )


async def _process_query_background(
    task_id: str,
    product: str,
    language: str,
    destination: str,
    use_cache: bool,
):
    try:
        if use_cache:
            query_hash = compute_query_hash(product, None, destination)
            cached = await check_cache(query_hash)
            if cached:
                await update_task(task_id, {
                    "status": "completed",
                    "flow": "trade_check",
                    "result": {"source": "cache", "data": cached},
                })
                logger.info("Cache HIT for %s", task_id)
                return

        callback = _progress_callback(task_id)
        result = await run_agent(product, max_tool_rounds=10, progress_callback=callback)

        if isinstance(result, dict):
            await update_task(task_id, {
                "status": "completed",
                "flow": result.get("intent") or result.get("flow", "trade_check"),
                "result": result,
            })
        else:
            await update_task(task_id, {
                "status": "completed",
                "flow": "trade_check",
                "result": {"answer": str(result)},
            })

        logger.info("Query completed: %s", task_id)

    except Exception as e:
        logger.error("Query failed %s: %s", task_id, e)
        try:
            await update_task(task_id, {"status": "error", "error": str(e)})
        except Exception:
            pass


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
    from app.supabase_client import get_service_client as _gsc
    supabase = _gsc()
    return {
        "status": "ok",
        "service": "Trade Price Service",
        "timestamp": datetime.now(),
        "supabase_connected": supabase is not None,
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
