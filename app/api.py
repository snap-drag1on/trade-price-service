from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Any
import uuid
import asyncio
from datetime import datetime

from app.agent.engine import run_agent
from app.agent.contract_v1_1 import LayerEvent, TradeIntake, create_clarification, normalize_legacy_message, resume_intake
from app.agent.contract_runner_v1_1 import run_contract_v1_1
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
    async def callback(phase: str, data: dict):
        ui_label = UI_PHASE_MAP.get(phase, {}).get("label", phase)
        phase_data = {**data, "ui_label": ui_label}
        try:
            await update_task(task_id, {"phases": {phase: phase_data}})
        except Exception as e:
            logger.warning("Progress update failed for %s: %s", phase, e)
    return callback


def _contract_event_callback(task_id: str):
    """Persist safe, idempotent Contract v1.1 events inside the existing JSON task store."""
    async def callback(event: LayerEvent):
        event_payload = event.model_dump(mode="json")
        phases: dict[str, dict] = {f"event_{event.sequence:06d}": event_payload}
        if event.layer_id:
            phases[f"layer_{event.layer_id}"] = {
                "status": "completed" if event.state == "complete" else event.state,
                "progress": 1.0 if event.state == "complete" else 0.0,
                "ui_label": event.layer_id,
                "label": event.message,
                "latest_event_id": event.event_id,
                "evidence_ids": list(event.evidence_ids),
                "detail": event.detail,
            }
        try:
            await update_task(task_id, {"phases": phases})
        except Exception as exc:
            logger.warning("Contract event update failed for %s: %s", task_id, exc)
    return callback


@router.post("/query", response_model=QueryResponse)
async def create_query(
    req: QueryRequest,
    background_tasks: BackgroundTasks,
) -> QueryResponse:
    task_id = str(uuid.uuid4())
    session_id = req.session_id or task_id
    intake = normalize_legacy_message(req.product, session_id, req.intake_sequence)
    if req.previous_task_id:
        previous_task = await get_task(req.previous_task_id)
        previous_snapshot = ((previous_task or {}).get("result") or {}).get("intake_snapshot")
        if not previous_snapshot:
            raise HTTPException(status_code=409, detail="The previous intake snapshot is unavailable. Please restart the trade check.")
        try:
            previous_intake = TradeIntake.model_validate(previous_snapshot)
            intake = resume_intake(previous_intake, req.product, session_id, req.intake_sequence)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=f"The clarification could not be resumed: {exc}") from exc
    clarification = create_clarification(intake)

    if clarification is not None:
        clarification_payload = clarification.model_dump(mode="json")
        await save_task(task_id, {
            "status": "needs_input",
            "flow": intake.intent.value,
            "phases": {},
            "result": {
                "kind": "clarification",
                "contract_version": "1.1",
                "intent": intake.intent.value,
                "intake_id": intake.intake_id,
                "clarification": clarification_payload,
                "intake_snapshot": intake.model_dump(mode="json"),
            },
        })
        return QueryResponse(
            success=True,
            task_id=task_id,
            status="needs_input",
            flow=intake.intent.value,
            clarification=clarification_payload,
            timestamp=datetime.now(),
        )

    await save_task(task_id, {
        "status": "processing",
        "flow": intake.intent.value,
        "phases": {},
        "result": {"intake_snapshot": intake.model_dump(mode="json")},
    })

    background_tasks.add_task(
        _process_contract_query_background,
        task_id=task_id,
        intake=intake,
        has_image=req.has_image,
    )

    return QueryResponse(
        success=True,
        task_id=task_id,
        status="processing",
        flow=intake.intent.value,
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
        clarification=(task_data.get("result") or {}).get("clarification") if task_data.get("status") == "needs_input" else None,
        error=task_data.get("error"),
        timestamp=datetime.now(),
    )


async def _process_contract_query_background(task_id: str, intake, has_image: bool):
    try:
        result = await asyncio.wait_for(
            run_contract_v1_1(intake, task_id, event_callback=_contract_event_callback(task_id), has_image=has_image),
            timeout=90,
        )
        result["intake_snapshot"] = intake.model_dump(mode="json")
        status = result.get("status", "completed")
        if status == "needs_input":
            await update_task(task_id, {"status": "needs_input", "flow": intake.intent.value, "result": result})
        else:
            await update_task(task_id, {"status": "completed", "flow": intake.intent.value, "result": result})
        logger.info("Contract v1.1 query completed: %s", task_id)

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
    import sqlite3, os, tempfile, json, httpx
    from app.supabase_client import get_service_client as _gsc
    from app.config import settings
    supabase = _gsc()
    db = os.path.join(tempfile.gettempdir(), "trade_tasks", "tasks.db")
    tasks = []
    if os.path.exists(db):
        try:
            conn = sqlite3.connect(db, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT task_id, status, timestamp FROM tasks ORDER BY timestamp DESC LIMIT 10")
            for row in cur:
                tasks.append({"id": row["task_id"][:12], "status": row["status"]})
            conn.close()
        except Exception:
            pass
    sb_task = False
    try:
        from app.task_store import _supabase_headers, _supabase_save, _supabase_get
        await _supabase_save("hb", {"status": "ok"})
        sb_task = await _supabase_get("hb") is not None
    except Exception:
        pass
    return {
        "status": "ok",
        "service": "Trade Price Service",
        "timestamp": datetime.now(),
        "supabase_connected": supabase is not None,
        "supabase_task_store": sb_task,
        "tasks": tasks,
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
