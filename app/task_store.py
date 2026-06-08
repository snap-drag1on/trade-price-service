from __future__ import annotations

import json
import os
import tempfile
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

from app.log import get_logger

logger = get_logger("task_store")

STORE_DIR = os.path.join(tempfile.gettempdir(), "trade_tasks")
os.makedirs(STORE_DIR, exist_ok=True)


def _path(task_id: str) -> str:
    return os.path.join(STORE_DIR, f"{task_id}.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def save_task(task_id: str, data: dict) -> None:
    path = _path(task_id)
    row = {
        "status": data.get("status", "processing") or "processing",
        "flow": data.get("flow", "") or "",
        "phases": data.get("phases", {}),
        "result": data.get("result"),
        "error": data.get("error"),
        "timestamp": _now_iso(),
    }
    try:
        with open(path, "w") as f:
            json.dump(row, f)
        logger.info("Task %s saved (status=%s)", task_id[:12], row["status"])
    except Exception as e:
        logger.error("Failed to save task %s: %s", task_id, e)
        raise


async def get_task(task_id: str) -> Optional[dict]:
    path = _path(task_id)
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Failed to read task %s: %s", task_id, e)
    return None


async def update_task(task_id: str, updates: dict) -> None:
    path = _path(task_id)
    try:
        data = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
        for k, v in updates.items():
            if k == "phases" and isinstance(v, dict):
                existing = data.get("phases", {})
                existing.update(v)
                data["phases"] = existing
            else:
                data[k] = v
        data["timestamp"] = _now_iso()
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning("Failed to update task %s: %s", task_id, e)


async def count_active_tasks() -> int:
    try:
        count = 0
        for fname in os.listdir(STORE_DIR):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(STORE_DIR, fname)
            try:
                with open(fpath, "r") as f:
                    data = json.load(f)
                if data.get("status") == "processing":
                    count += 1
            except Exception:
                pass
        return count
    except Exception as e:
        logger.warning("Failed to count tasks: %s", e)
        return 0
