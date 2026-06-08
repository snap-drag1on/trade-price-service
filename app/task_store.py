from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

from app.supabase_client import get_service_client
from app.log import get_logger

logger = get_logger("task_store")

MEMORY: dict[str, dict] = {}
MEMORY_TIMESTAMPS: dict[str, float] = {}
_reported_no_supabase = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_memory(task_id: str, data: dict) -> None:
    MEMORY[task_id] = {
        "status": data.get("status", "processing") or "processing",
        "flow": data.get("flow", "") or "",
        "phases": data.get("phases", {}),
        "result": data.get("result"),
        "error": data.get("error"),
    }
    MEMORY_TIMESTAMPS[task_id] = datetime.now(timezone.utc).timestamp()


async def _write_supabase(row: dict) -> bool:
    supabase = get_service_client()
    if supabase is None:
        return False
    try:
        supabase.table("task_store").upsert(row).execute()
        return True
    except Exception as e:
        logger.warning("Supabase write failed: %s", e)
        return False


async def save_task(task_id: str, data: dict) -> None:
    global _reported_no_supabase
    row = {
        "task_id": task_id,
        "status": data.get("status", "processing") or "processing",
        "flow": data.get("flow", "") or "",
        "phases": data.get("phases", {}),
        "result": data.get("result"),
        "error": data.get("error"),
    }
    ok = await _write_supabase(row)
    if not ok and not _reported_no_supabase:
        logger.warning("Supabase unavailable — using in-memory task store")
        _reported_no_supabase = True
    _to_memory(task_id, row)


async def get_task(task_id: str) -> Optional[dict]:
    if task_id in MEMORY:
        m = MEMORY[task_id]
        return {
            "status": m.get("status", "unknown"),
            "flow": m.get("flow", ""),
            "phases": m.get("phases", {}),
            "result": m.get("result"),
            "error": m.get("error"),
            "timestamp": _now_iso(),
        }
    supabase = get_service_client()
    if supabase is None:
        return None
    try:
        result = supabase.table("task_store").select("*").eq("task_id", task_id).limit(1).execute()
        if result.data and len(result.data) > 0:
            row = result.data[0]
            phases = row.get("phases", {})
            if isinstance(phases, str):
                phases = json.loads(phases)
            result_data = row.get("result")
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
            return {
                "status": row.get("status", "unknown") or "unknown",
                "flow": row.get("flow", "") or "",
                "phases": phases or {},
                "result": result_data,
                "error": row.get("error"),
                "timestamp": row.get("timestamp", _now_iso()),
            }
    except Exception as e:
        logger.warning("Supabase read failed: %s", e)
    return None


async def update_task(task_id: str, updates: dict) -> None:
    if task_id in MEMORY:
        m = MEMORY[task_id]
        for k, v in updates.items():
            if k == "phases" and isinstance(v, dict):
                existing = m.get("phases", {})
                existing.update(v)
                m["phases"] = existing
            else:
                m[k] = v
        MEMORY_TIMESTAMPS[task_id] = datetime.now(timezone.utc).timestamp()
    else:
        _to_memory(task_id, {"status": "processing", "flow": "", "phases": {}, "result": None, "error": None})
        m = MEMORY[task_id]
        for k, v in updates.items():
            if k == "phases" and isinstance(v, dict):
                existing = m.get("phases", {})
                existing.update(v)
                m["phases"] = existing
            else:
                m[k] = v
        MEMORY_TIMESTAMPS[task_id] = datetime.now(timezone.utc).timestamp()
    supabase = get_service_client()
    if supabase is None:
        return
    try:
        current = await get_task(task_id)
        if current is None:
            return
        merged_phases = dict(current.get("phases", {}) or {})
        if "phases" in updates and isinstance(updates["phases"], dict):
            merged_phases.update(updates["phases"])
        update_data = {"timestamp": _now_iso()}
        for key in ("phases", "status", "flow", "result", "error"):
            if key in updates:
                update_data[key] = updates[key]
        supabase.table("task_store").update(update_data).eq("task_id", task_id).execute()
    except Exception as e:
        logger.warning("Supabase update failed: %s", e)


async def count_active_tasks() -> int:
    memory_count = sum(1 for v in MEMORY.values() if v.get("status") == "processing")
    supabase = get_service_client()
    if supabase is None:
        return memory_count
    try:
        result = supabase.table("task_store").select("task_id", count="exact").eq("status", "processing").execute()
        return memory_count + (result.count or 0)
    except Exception as e:
        logger.warning("Failed to count tasks: %s", e)
        return memory_count
