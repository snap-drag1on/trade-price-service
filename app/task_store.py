from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from app.log import get_logger

logger = get_logger("task_store")

DB_DIR = os.path.join(tempfile.gettempdir(), "trade_tasks")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "tasks.db")

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA busy_timeout=5000")
        _local.conn.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "  task_id TEXT PRIMARY KEY,"
            "  status TEXT DEFAULT 'processing',"
            "  flow TEXT DEFAULT '',"
            "  phases TEXT DEFAULT '{}',"
            "  result TEXT,"
            "  error TEXT,"
            "  timestamp TEXT"
            ")"
        )
        _local.conn.commit()
    return _local.conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def save_task(task_id: str, data: dict) -> None:
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO tasks (task_id, status, flow, phases, result, error, timestamp) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                task_id,
                data.get("status", "processing") or "processing",
                data.get("flow", "") or "",
                json.dumps(data.get("phases", {})),
                json.dumps(data.get("result")) if data.get("result") else None,
                data.get("error"),
                _now_iso(),
            ),
        )
        conn.commit()
        logger.info("Task %s saved (status=%s)", task_id[:12], data.get("status"))
    except Exception as e:
        logger.error("Failed to save task %s: %s", task_id, e)
        raise


async def get_task(task_id: str) -> Optional[dict]:
    try:
        conn = _get_conn()
        cur = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,))
        row = cur.fetchone()
        if row:
            return {
                "status": row["status"] or "unknown",
                "flow": row["flow"] or "",
                "phases": json.loads(row["phases"]) if row["phases"] else {},
                "result": json.loads(row["result"]) if row["result"] else None,
                "error": row["error"],
                "timestamp": row["timestamp"] or _now_iso(),
            }
    except Exception as e:
        logger.warning("Failed to read task %s: %s", task_id, e)
    return None


async def update_task(task_id: str, updates: dict) -> None:
    try:
        conn = _get_conn()
        current = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not current:
            logger.warning("Task %s not found for update", task_id[:12])
            return
        phases = json.loads(current["phases"]) if current["phases"] else {}
        if "phases" in updates and isinstance(updates["phases"], dict):
            phases.update(updates["phases"])
        status = updates.get("status", current["status"])
        flow = updates.get("flow", current["flow"] or "")
        result = json.dumps(updates["result"]) if "result" in updates and updates["result"] else current["result"]
        error = updates.get("error", current["error"])
        conn.execute(
            "UPDATE tasks SET status=?, flow=?, phases=?, result=?, error=?, timestamp=? WHERE task_id=?",
            (status, flow, json.dumps(phases), result, error, _now_iso(), task_id),
        )
        conn.commit()
    except Exception as e:
        logger.warning("Failed to update task %s: %s", task_id, e)


async def count_active_tasks() -> int:
    try:
        conn = _get_conn()
        cur = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status='processing'")
        row = cur.fetchone()
        return row["c"] if row else 0
    except Exception as e:
        logger.warning("Failed to count tasks: %s", e)
        return 0
