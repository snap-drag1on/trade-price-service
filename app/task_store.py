from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.supabase_client import get_service_client
from app.log import get_logger

logger = get_logger("task_store")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def save_task(task_id: str, data: dict) -> None:
    supabase = get_service_client()
    if supabase is None:
        logger.warning("Supabase unavailable, task %s not saved", task_id)
        return
    try:
        row = {
            "task_id": task_id,
            "status": data.get("status", "processing") or "processing",
            "flow": data.get("flow", "") or "",
            "phases": data.get("phases", {}),
            "result": data.get("result"),
            "error": data.get("error"),
        }
        supabase.table("task_store").upsert(row).execute()
        logger.info("Task %s saved (status=%s)", task_id[:12], row["status"])
    except Exception as e:
        logger.warning("Failed to save task %s: %s", task_id, e)


async def get_task(task_id: str) -> Optional[dict]:
    supabase = get_service_client()
    if supabase is None:
        logger.warning("Supabase unavailable for task %s", task_id)
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
        logger.warning("Failed to get task %s: %s", task_id, e)
    return None


async def update_task(task_id: str, updates: dict) -> None:
    supabase = get_service_client()
    if supabase is None:
        return
    try:
        current = await get_task(task_id)
        if current is None:
            logger.warning("Task %s not found for update", task_id[:12])
            return
        merged_phases = dict(current.get("phases", {}) or {})
        if "phases" in updates and isinstance(updates["phases"], dict):
            merged_phases.update(updates["phases"])
        update_data = {
            "phases": merged_phases,
            "timestamp": _now_iso(),
        }
        for key in ("status", "flow", "result", "error"):
            if key in updates:
                update_data[key] = updates[key]
        supabase.table("task_store").update(update_data).eq("task_id", task_id).execute()
    except Exception as e:
        logger.warning("Failed to update task %s: %s", task_id, e)


async def count_active_tasks() -> int:
    supabase = get_service_client()
    if supabase is None:
        return 0
    try:
        result = supabase.table("task_store").select("task_id", count="exact").eq("status", "processing").execute()
        return result.count or 0
    except Exception as e:
        logger.warning("Failed to count tasks: %s", e)
        return 0
