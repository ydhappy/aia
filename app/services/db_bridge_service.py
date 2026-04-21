import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None

try:
    import pymysql
except Exception:  # pragma: no cover
    pymysql = None


SCHEMA_SQL = """
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS robot_event (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    tick INTEGER,
    event_type TEXT,
    severity TEXT,
    message TEXT,
    payload_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS robot_feedback (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    tick INTEGER,
    action TEXT,
    reward REAL,
    outcome TEXT,
    map_id INTEGER,
    context_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS robot_decision (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    tick INTEGER,
    action TEXT,
    action_args_json TEXT,
    confidence REAL,
    source TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS robot_trace_summary (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    tick INTEGER,
    trace_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class DBBridgeService:
    def __init__(self) -> None:
        self.backend = settings.db_bridge_backend.lower()
        self.sqlite_path = Path(settings.db_bridge_sqlite_path)
        self.postgres_dsn = settings.db_bridge_postgres_dsn
        self.mysql_dsn = settings.db_bridge_mysql_dsn
        if self.backend == "sqlite":
            self._init_sqlite_schema()
        elif self.backend == "postgresql":
            self._init_postgres_schema()
        elif self.backend == "mysql":
            self._init_mysql_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _pg_connect(self):
        if psycopg is None:
            raise RuntimeError("psycopg_not_installed")
        return psycopg.connect(self.postgres_dsn)

    def _mysql_connect(self):
        if pymysql is None:
            raise RuntimeError("pymysql_not_installed")
        parsed = urlparse(self.mysql_dsn.replace("mysql+pymysql://", "mysql://"))
        return pymysql.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 3306,
            user=parsed.username or "root",
            password=parsed.password or "",
            database=(parsed.path or "/aia").lstrip("/"),
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )

    def _init_sqlite_schema(self) -> None:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def _init_postgres_schema(self) -> None:
        if psycopg is None:
            return
        ddl = (
            SCHEMA_SQL.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
            .replace("INTEGER PRIMARY KEY", "BIGSERIAL PRIMARY KEY")
            .replace("REAL", "DOUBLE PRECISION")
        )
        with self._pg_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()

    def _init_mysql_schema(self) -> None:
        if pymysql is None:
            return
        ddl = (
            SCHEMA_SQL.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGINT PRIMARY KEY AUTO_INCREMENT")
            .replace("INTEGER PRIMARY KEY", "BIGINT PRIMARY KEY AUTO_INCREMENT")
            .replace("INTEGER", "INT")
            .replace("REAL", "DOUBLE")
            .replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        )
        with self._mysql_connect() as conn:
            with conn.cursor() as cur:
                for stmt in [s.strip() for s in ddl.split(';') if s.strip()]:
                    cur.execute(stmt)

    def poll_states(self) -> list[dict]:
        if self.backend == "sqlite":
            with self._connect() as conn:
                rows = conn.execute("SELECT * FROM robot_state ORDER BY updated_at DESC LIMIT 500").fetchall()
                return [dict(row) for row in rows]
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM robot_state ORDER BY updated_at DESC LIMIT 500")
                    cols = [d.name for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM robot_state ORDER BY updated_at DESC LIMIT 500")
                    return list(cur.fetchall())
        return []

    def poll_events(self) -> list[dict]:
        if self.backend == "sqlite":
            with self._connect() as conn:
                rows = conn.execute("SELECT * FROM robot_event ORDER BY id DESC LIMIT 500").fetchall()
                return [dict(row) for row in rows]
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM robot_event ORDER BY id DESC LIMIT 500")
                    cols = [d.name for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM robot_event ORDER BY id DESC LIMIT 500")
                    return list(cur.fetchall())
        return []

    def poll_feedback(self) -> list[dict]:
        if self.backend == "sqlite":
            with self._connect() as conn:
                rows = conn.execute("SELECT * FROM robot_feedback ORDER BY id DESC LIMIT 500").fetchall()
                return [dict(row) for row in rows]
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM robot_feedback ORDER BY id DESC LIMIT 500")
                    cols = [d.name for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM robot_feedback ORDER BY id DESC LIMIT 500")
                    return list(cur.fetchall())
        return []

    def write_decision(self, decision_row: dict) -> dict:
        if self.backend == "sqlite":
            with self._connect() as conn:
                conn.execute("INSERT INTO robot_decision (agent_id, tick, action, action_args_json, confidence, source, reason) VALUES (?, ?, ?, ?, ?, ?, ?)", (decision_row.get("agent_id"), decision_row.get("tick"), decision_row.get("action"), json.dumps(decision_row.get("action_args", {})), decision_row.get("confidence"), decision_row.get("source"), decision_row.get("reason")))
            return {"written": True, "row": decision_row}
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO robot_decision (agent_id, tick, action, action_args_json, confidence, source, reason) VALUES (%s, %s, %s, %s, %s, %s, %s)", (decision_row.get("agent_id"), decision_row.get("tick"), decision_row.get("action"), json.dumps(decision_row.get("action_args", {})), decision_row.get("confidence"), decision_row.get("source"), decision_row.get("reason")))
                conn.commit()
            return {"written": True, "row": decision_row}
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO robot_decision (agent_id, tick, action, action_args_json, confidence, source, reason) VALUES (%s, %s, %s, %s, %s, %s, %s)", (decision_row.get("agent_id"), decision_row.get("tick"), decision_row.get("action"), json.dumps(decision_row.get("action_args", {})), decision_row.get("confidence"), decision_row.get("source"), decision_row.get("reason")))
            return {"written": True, "row": decision_row}
        return {"written": False, "reason": "unsupported_backend", "row": decision_row}

    def write_trace_summary(self, trace_row: dict) -> dict:
        if self.backend == "sqlite":
            with self._connect() as conn:
                conn.execute("INSERT INTO robot_trace_summary (agent_id, tick, trace_json) VALUES (?, ?, ?)", (trace_row.get("agent_id"), trace_row.get("tick"), json.dumps(trace_row.get("trace", {}))))
            return {"written": True, "row": trace_row}
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO robot_trace_summary (agent_id, tick, trace_json) VALUES (%s, %s, %s)", (trace_row.get("agent_id"), trace_row.get("tick"), json.dumps(trace_row.get("trace", {}))))
                conn.commit()
            return {"written": True, "row": trace_row}
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO robot_trace_summary (agent_id, tick, trace_json) VALUES (%s, %s, %s)", (trace_row.get("agent_id"), trace_row.get("tick"), json.dumps(trace_row.get("trace", {}))))
            return {"written": True, "row": trace_row}
        return {"written": False, "reason": "unsupported_backend", "row": trace_row}


db_bridge_service = DBBridgeService()
