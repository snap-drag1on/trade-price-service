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


def _supabase_headers() -> Optional[dict]:
    try:
        from app.config import settings
        key = settings.supabase_service_key or settings.supabase_anon_key
        if not key:
            return None
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
    except Exception:
        return None


async def _supabase_save(task_id: str, data: dict) -> None:
    import httpx
    try:
        headers = _supabase_headers()
        if headers is None:
            return
        from app.config import settings
        url = f"{settings.supabase_url}/rest/v1/task_store"
        payload = {
            "task_id": task_id,
            "status": data.get("status", "processing") or "processing",
            "flow": data.get("flow", "") or "",
            "phases": json.dumps(data.get("phases", {})),
            "result": json.dumps(data.get("result")) if data.get("result") else None,
            "error": data.get("error"),
            "timestamp": _now_iso(),
        }
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(f"{url}?on_conflict=task_id", headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                logger.debug("Supabase save returned %d: %s", resp.status_code, resp.text[:100])
    except Exception as e:
        logger.debug("Supabase task save failed: %s", e)


async def _supabase_get(task_id: str) -> Optional[dict]:
    import httpx
    try:
        headers = _supabase_headers()
        if headers is None:
            return None
        from app.config import settings
        url = f"{settings.supabase_url}/rest/v1/task_store"
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{url}?task_id=eq.{task_id}&select=*",
                headers=headers,
            )
            if resp.status_code == 200:
                rows = resp.json()
                if rows and len(rows) > 0:
                    row = rows[0]
                    return {
                        "status": row.get("status", "unknown"),
                        "flow": row.get("flow", ""),
                        "phases": json.loads(row["phases"]) if row.get("phases") else {},
                        "result": json.loads(row["result"]) if row.get("result") else None,
                        "error": row.get("error"),
                        "timestamp": row.get("timestamp", _now_iso()),
                    }
    except Exception as e:
        logger.debug("Supabase task get failed: %s", e)
    return None


async def _supabase_update(task_id: str, updates: dict) -> None:
    import httpx
    try:
        headers = _supabase_headers()
        if headers is None:
            return
        current = await _supabase_get(task_id)
        if not current:
            return
        from app.config import settings
        url = f"{settings.supabase_url}/rest/v1/task_store"
        phases = dict(current.get("phases", {}))
        if "phases" in updates and isinstance(updates["phases"], dict):
            phases.update(updates["phases"])
        status = updates.get("status", current["status"])
        flow = updates.get("flow", current.get("flow", ""))
        result = json.dumps(updates["result"]) if "result" in updates and updates["result"] else (json.dumps(current["result"]) if current.get("result") else None)
        error = updates.get("error", current.get("error"))
        payload = {
            "task_id": task_id,
            "status": status,
            "flow": flow,
            "phases": json.dumps(phases),
            "result": result,
            "error": error,
            "timestamp": _now_iso(),
        }
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(f"{url}?on_conflict=task_id", headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                logger.debug("Supabase update returned %d: %s", resp.status_code, resp.text[:100])
    except Exception as e:
        logger.debug("Supabase task update failed: %s", e)


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

    await _supabase_save(task_id, data)


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

    sb_result = await _supabase_get(task_id)
    if sb_result:
        try:
            conn = _get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO tasks (task_id, status, flow, phases, result, error, timestamp) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    task_id,
                    sb_result.get("status", "unknown"),
                    sb_result.get("flow", ""),
                    json.dumps(sb_result.get("phases", {})),
                    json.dumps(sb_result.get("result")) if sb_result.get("result") else None,
                    sb_result.get("error"),
                    sb_result.get("timestamp", _now_iso()),
                ),
            )
            conn.commit()
        except Exception:
            pass
        return sb_result

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

    await _supabase_update(task_id, updates)


async def count_active_tasks() -> int:
    try:
        conn = _get_conn()
        cur = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status='processing'")
        row = cur.fetchone()
        return row["c"] if row else 0
    except Exception as e:
        logger.warning("Failed to count tasks: %s", e)
        return 0
