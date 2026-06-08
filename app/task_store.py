from __future__ import annotations

import json
import os
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional
from pathlib import Path

from app.log import get_logger

logger = get_logger("task_store")

TASK_DIR = Path("/tmp/trade_tasks")

_lock = asyncio.Lock()


def _ensure_dir():
    TASK_DIR.mkdir(parents=True, exist_ok=True)


def _path(task_id: str) -> Path:
    return TASK_DIR / f"{task_id}.json"


async def save_task(task_id: str, data: dict) -> None:
    async with _lock:
        _ensure_dir()
        try:
            entry = {
                "task_id": task_id,
                "status": data.get("status", "processing"),
                "flow": data.get("flow", ""),
                "phases": data.get("phases", {}),
                "result": data.get("result"),
                "error": data.get("error"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            _path(task_id).write_text(json.dumps(entry, ensure_ascii=False))
            logger.info("Task %s saved", task_id[:12])
        except Exception as e:
            logger.error("Failed to save task %s: %s", task_id, e)


async def get_task(task_id: str) -> Optional[dict]:
    async with _lock:
        try:
            p = _path(task_id)
            if not p.exists():
                return None
            return json.loads(p.read_text())
        except Exception as e:
            logger.warning("Failed to read task %s: %s", task_id, e)
            return None


async def update_task(task_id: str, updates: dict) -> None:
    async with _lock:
        try:
            p = _path(task_id)
            if not p.exists():
                logger.warning("Task %s not found for update", task_id[:12])
                return
            entry = json.loads(p.read_text())
            for key in ("status", "flow", "result", "error"):
                if key in updates:
                    entry[key] = updates[key]
            if "phases" in updates and isinstance(updates["phases"], dict):
                entry.setdefault("phases", {}).update(updates["phases"])
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
            p.write_text(json.dumps(entry, ensure_ascii=False))
        except Exception as e:
            logger.warning("Failed to update task %s: %s", task_id, e)


async def count_active_tasks() -> int:
    async with _lock:
        _ensure_dir()
        count = 0
        for f in TASK_DIR.iterdir():
            if f.suffix == ".json":
                try:
                    entry = json.loads(f.read_text())
                    if entry.get("status") == "processing":
                        count += 1
                except Exception:
                    pass
        return count
