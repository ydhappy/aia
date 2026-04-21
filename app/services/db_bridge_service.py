import json
import sqlite3
from pathlib import Path

from app.core.config import settings


class DBBridgeService:
    def __init__(self) -> None:
        self.backend = settings.db_bridge_backend.lower()
        self.sqlite_path = Path(settings.db_bridge_sqlite_path)
        if self.backend == "sqlite":
            self._init_sqlite_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite_schema(self) -> None:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS robot_state (
                    agent_id TEXT PRIMARY KEY,
                    tick INTEGER,
                    hp INTEGER,
                    mp INTEGER,
                    x INTEGER,
                    y INTEGER,
                    map_id INTEGER,
                    target_id TEXT,
                    target_distance INTEGER,
                    safe_zone INTEGER,
                    weight_percent INTEGER,
                    payload_json TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS robot_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    tick INTEGER,
                    event_type TEXT,
                    severity TEXT,
                    message TEXT,
                    payload_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS robot_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    tick INTEGER,
                    action TEXT,
                    reward REAL,
                    outcome TEXT,
                    map_id INTEGER,
                    context_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS robot_decision (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    tick INTEGER,
                    action TEXT,
                    action_args_json TEXT,
                    confidence REAL,
                    source TEXT,
                    reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS robot_trace_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    tick INTEGER,
                    trace_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def poll_states(self) -> list[dict]:
        if self.backend != "sqlite":
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM robot_state ORDER BY updated_at DESC LIMIT 500").fetchall()
            return [dict(row) for row in rows]

    def poll_events(self) -> list[dict]:
        if self.backend != "sqlite":
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM robot_event ORDER BY id DESC LIMIT 500").fetchall()
            return [dict(row) for row in rows]

    def poll_feedback(self) -> list[dict]:
        if self.backend != "sqlite":
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM robot_feedback ORDER BY id DESC LIMIT 500").fetchall()
            return [dict(row) for row in rows]

    def write_decision(self, decision_row: dict) -> dict:
        if self.backend != "sqlite":
            return {"written": False, "reason": "unsupported_backend", "row": decision_row}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO robot_decision (agent_id, tick, action, action_args_json, confidence, source, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_row.get("agent_id"),
                    decision_row.get("tick"),
                    decision_row.get("action"),
                    json.dumps(decision_row.get("action_args", {})),
                    decision_row.get("confidence"),
                    decision_row.get("source"),
                    decision_row.get("reason"),
                ),
            )
        return {"written": True, "row": decision_row}

    def write_trace_summary(self, trace_row: dict) -> dict:
        if self.backend != "sqlite":
            return {"written": False, "reason": "unsupported_backend", "row": trace_row}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO robot_trace_summary (agent_id, tick, trace_json)
                VALUES (?, ?, ?)
                """,
                (
                    trace_row.get("agent_id"),
                    trace_row.get("tick"),
                    json.dumps(trace_row.get("trace", {})),
                ),
            )
        return {"written": True, "row": trace_row}


db_bridge_service = DBBridgeService()
