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
CREATE TABLE IF NOT EXISTS aia_robot_state (
    robot_uid INTEGER NOT NULL PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    hp INTEGER NOT NULL DEFAULT 0,
    mp INTEGER NOT NULL DEFAULT 0,
    hp_percent INTEGER NOT NULL DEFAULT 0,
    ai_status INTEGER NOT NULL DEFAULT 0,
    mode INTEGER NOT NULL DEFAULT -1,
    mode_label TEXT NOT NULL DEFAULT '',
    stall_count INTEGER NOT NULL DEFAULT 0,
    nav_fail INTEGER NOT NULL DEFAULT 0,
    last_active TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS aia_robot_event (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER NOT NULL DEFAULT 0,
    name TEXT NOT NULL DEFAULT '',
    action_type TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '',
    loc_x INTEGER NOT NULL DEFAULT 0,
    loc_y INTEGER NOT NULL DEFAULT 0,
    loc_map INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS aia_robot_feedback (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL DEFAULT '',
    tick INTEGER,
    action TEXT NOT NULL DEFAULT '',
    reward REAL,
    outcome TEXT,
    map_id INTEGER NOT NULL DEFAULT 0,
    context_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS aia_robot_decision (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL DEFAULT '',
    tick INTEGER,
    action TEXT NOT NULL DEFAULT '',
    action_args_json TEXT,
    confidence REAL,
    source TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS aia_robot_trace_summary (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL DEFAULT '',
    tick INTEGER,
    trace_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


MYSQL_BRIDGE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS aia_robot_state (
    robot_uid BIGINT(20) UNSIGNED NOT NULL,
    name VARCHAR(45) NOT NULL DEFAULT '',
    hp INT(10) NOT NULL DEFAULT 0,
    mp INT(10) NOT NULL DEFAULT 0,
    hp_percent INT(10) NOT NULL DEFAULT 0,
    ai_status INT(10) NOT NULL DEFAULT 0,
    mode INT(10) NOT NULL DEFAULT -1,
    mode_label VARCHAR(30) NOT NULL DEFAULT '',
    stall_count INT(10) NOT NULL DEFAULT 0,
    nav_fail INT(10) NOT NULL DEFAULT 0,
    last_active DATETIME NULL DEFAULT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (robot_uid),
    KEY idx_aia_robot_state_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE IF NOT EXISTS aia_robot_event (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    name VARCHAR(45) NOT NULL DEFAULT '',
    action_type VARCHAR(40) NOT NULL DEFAULT '',
    detail VARCHAR(255) NOT NULL DEFAULT '',
    loc_x INT(10) NOT NULL DEFAULT 0,
    loc_y INT(10) NOT NULL DEFAULT 0,
    loc_map INT(10) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_event_object (object_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE IF NOT EXISTS aia_robot_feedback (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    tick BIGINT(20) NULL,
    action VARCHAR(32) NOT NULL DEFAULT '',
    reward DOUBLE NULL,
    outcome VARCHAR(32) NULL,
    map_id INT(10) NOT NULL DEFAULT 0,
    context_json LONGTEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_feedback_agent (agent_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE IF NOT EXISTS aia_robot_decision (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    tick BIGINT(20) NULL,
    action VARCHAR(32) NOT NULL DEFAULT '',
    action_args_json LONGTEXT NULL,
    confidence DOUBLE NULL,
    source VARCHAR(64) NULL,
    reason VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_decision_agent (agent_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE IF NOT EXISTS aia_robot_trace_summary (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    tick BIGINT(20) NULL,
    trace_json LONGTEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_trace_agent (agent_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class DBBridgeService:
    def __init__(self) -> None:
        self.backend = settings.db_bridge_backend.lower()
        self.sqlite_path = Path(settings.db_bridge_sqlite_path)
        self.postgres_dsn = settings.db_bridge_postgres_dsn
        self.mysql_dsn = settings.db_bridge_mysql_dsn
        self.poll_limit = max(1, settings.db_bridge_poll_limit)
        self.write_batch_size = max(1, settings.db_bridge_write_batch_size)
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
            charset="utf8",
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
        with self._mysql_connect() as conn:
            with conn.cursor() as cur:
                for stmt in [s.strip() for s in MYSQL_BRIDGE_SCHEMA_SQL.split(';') if s.strip()]:
                    cur.execute(stmt)

    def poll_states(self) -> list[dict]:
        limit = self.poll_limit
        if self.backend == "sqlite":
            with self._connect() as conn:
                rows = conn.execute(f"SELECT * FROM aia_robot_state ORDER BY updated_at DESC LIMIT {limit}").fetchall()
                return [dict(row) for row in rows]
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM aia_robot_state ORDER BY updated_at DESC LIMIT %s", (limit,))
                    cols = [d.name for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM aia_robot_state ORDER BY updated_at DESC LIMIT %s", (limit,))
                    return list(cur.fetchall())
        return []

    def poll_events(self) -> list[dict]:
        limit = self.poll_limit
        if self.backend == "sqlite":
            with self._connect() as conn:
                rows = conn.execute(f"SELECT * FROM aia_robot_event ORDER BY uid DESC LIMIT {limit}").fetchall()
                return [dict(row) for row in rows]
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM aia_robot_event ORDER BY uid DESC LIMIT %s", (limit,))
                    cols = [d.name for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM aia_robot_event ORDER BY uid DESC LIMIT %s", (limit,))
                    return list(cur.fetchall())
        return []

    def poll_feedback(self) -> list[dict]:
        limit = self.poll_limit
        if self.backend == "sqlite":
            with self._connect() as conn:
                rows = conn.execute(f"SELECT * FROM aia_robot_feedback ORDER BY uid DESC LIMIT {limit}").fetchall()
                return [dict(row) for row in rows]
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM aia_robot_feedback ORDER BY uid DESC LIMIT %s", (limit,))
                    cols = [d.name for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM aia_robot_feedback ORDER BY uid DESC LIMIT %s", (limit,))
                    return list(cur.fetchall())
        return []

    def _decision_values(self, rows: list[dict]) -> list[tuple]:
        limited = rows[: self.write_batch_size]
        return [(
            row.get("agent_id"),
            row.get("tick"),
            row.get("action"),
            json.dumps(row.get("action_args", {}), ensure_ascii=False),
            row.get("confidence"),
            row.get("source"),
            row.get("reason"),
        ) for row in limited]

    def _trace_values(self, rows: list[dict]) -> list[tuple]:
        limited = rows[: self.write_batch_size]
        return [(
            row.get("agent_id"),
            row.get("tick"),
            json.dumps(row.get("trace", {}), ensure_ascii=False),
        ) for row in limited]

    def write_decision(self, decision_row: dict) -> dict:
        return self.write_decisions_batch([decision_row])

    def write_trace_summary(self, trace_row: dict) -> dict:
        return self.write_traces_batch([trace_row])

    def write_decisions_batch(self, rows: list[dict]) -> dict:
        values = self._decision_values(rows)
        if self.backend == "sqlite":
            with self._connect() as conn:
                conn.executemany("INSERT INTO aia_robot_decision (agent_id, tick, action, action_args_json, confidence, source, reason) VALUES (?, ?, ?, ?, ?, ?, ?)", values)
            return {"written": True, "count": len(values)}
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.executemany("INSERT INTO aia_robot_decision (agent_id, tick, action, action_args_json, confidence, source, reason) VALUES (%s, %s, %s, %s, %s, %s, %s)", values)
                conn.commit()
            return {"written": True, "count": len(values)}
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.executemany("INSERT INTO aia_robot_decision (agent_id, tick, action, action_args_json, confidence, source, reason) VALUES (%s, %s, %s, %s, %s, %s, %s)", values)
            return {"written": True, "count": len(values)}
        return {"written": False, "reason": "unsupported_backend", "count": 0}

    def write_traces_batch(self, rows: list[dict]) -> dict:
        values = self._trace_values(rows)
        if self.backend == "sqlite":
            with self._connect() as conn:
                conn.executemany("INSERT INTO aia_robot_trace_summary (agent_id, tick, trace_json) VALUES (?, ?, ?)", values)
            return {"written": True, "count": len(values)}
        if self.backend == "postgresql" and psycopg is not None:
            with self._pg_connect() as conn:
                with conn.cursor() as cur:
                    cur.executemany("INSERT INTO aia_robot_trace_summary (agent_id, tick, trace_json) VALUES (%s, %s, %s)", values)
                conn.commit()
            return {"written": True, "count": len(values)}
        if self.backend == "mysql" and pymysql is not None:
            with self._mysql_connect() as conn:
                with conn.cursor() as cur:
                    cur.executemany("INSERT INTO aia_robot_trace_summary (agent_id, tick, trace_json) VALUES (%s, %s, %s)", values)
            return {"written": True, "count": len(values)}
        return {"written": False, "reason": "unsupported_backend", "count": 0}


db_bridge_service = DBBridgeService()
