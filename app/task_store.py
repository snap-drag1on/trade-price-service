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
            "status": data.get("status", "processing"),
            "flow": data.get("flow", ""),
            "phases": json.dumps(data.get("phases", {}), ensure_ascii=False),
            "result": json.dumps(data.get("result"), ensure_ascii=False) if data.get("result") else None,
            "error": data.get("error"),
            "timestamp": _now_iso(),
        }
        supabase.table("task_store").upsert(row, on_conflict=["task_id"]).execute()
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
            return {
                "status": row.get("status", "unknown"),
                "flow": row.get("flow", ""),
                "phases": json.loads(row.get("phases", "{}")) if row.get("phases") else {},
                "result": json.loads(row.get("result")) if row.get("result") else None,
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
        update_data = {"timestamp": _now_iso()}
        if "status" in updates:
            update_data["status"] = updates["status"]
        if "flow" in updates:
            update_data["flow"] = updates["flow"]
        if "phases" in updates:
            current = await get_task(task_id)
            merged = (current or {}).get("phases", {}) or {}
            if isinstance(updates["phases"], dict):
                merged.update(updates["phases"])
            update_data["phases"] = json.dumps(merged, ensure_ascii=False)
        if "result" in updates:
            update_data["result"] = json.dumps(updates["result"], ensure_ascii=False)
        if "error" in updates:
            update_data["error"] = updates["error"]
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
