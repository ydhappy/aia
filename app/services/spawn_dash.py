from __future__ import annotations

from datetime import datetime, timedelta

from app.core.config import settings
from app.core.mysql import connect_mysql
from app.core.names import SpawnStatus, Table
from app.ui.spawn_queue import render_spawn_queue


class SpawnRequestDashboardService:
    def _connect(self):
        return connect_mysql(settings.db_bridge_mysql_dsn)

    def summary(self, limit: int = 30, status: str | None = None, server_name: str | None = None) -> dict:
        limit = max(1, min(int(limit or 30), 200))
        status = self._clean_status(status)
        server_name = self._clean_optional_server(server_name)
        if settings.db_bridge_backend.lower() != "mysql":
            return self._summary(False, "db_bridge_backend_not_mysql", status, server_name)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    counts = self._counts(cur, server_name)
                    rows = self._rows(cur, limit, status, server_name)
            total = sum(counts.values())
            attention = counts.get(SpawnStatus.FAILED, 0) + counts.get(SpawnStatus.CLAIMED, 0)
            return self._summary(True, "", status, server_name, counts, total, attention, rows)
        except Exception as exc:
            return self._summary(False, str(exc), status, server_name, hint="Check MySQL connection, table sql/aia_robot_spawn_request_mysql55.sql, and DB user permissions.")

    def retry_failed(self, server_name: str = "main", limit: int = 50) -> dict:
        return self._reset(SpawnStatus.FAILED, "retry_failed", server_name, limit)

    def recover_stale_claimed(self, server_name: str = "main", older_than_minutes: int = 10, limit: int = 50) -> dict:
        limit = max(1, min(int(limit or 50), 500))
        older_than_minutes = max(1, min(int(older_than_minutes or 10), 1440))
        server_name = self._clean_server(server_name)
        if settings.db_bridge_backend.lower() != "mysql":
            return {"accepted": False, "action": "recover_stale_claimed", "server_name": server_name, "limit": limit, "older_than_minutes": older_than_minutes, "reason": "db_bridge_backend_not_mysql", "updated": 0}
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE %s SET status = %%s, claimed_at = NULL, last_error = %%s WHERE status = %%s AND server_name = %%s AND claimed_at IS NOT NULL AND claimed_at < %%s ORDER BY uid ASC LIMIT %%s" % Table.SPAWN,
                        (SpawnStatus.PENDING, "recovered_stale_claimed", SpawnStatus.CLAIMED, server_name, datetime.now() - timedelta(minutes=older_than_minutes), limit),
                    )
                    updated = int(cur.rowcount or 0)
            return {"accepted": True, "action": "recover_stale_claimed", "server_name": server_name, "limit": limit, "older_than_minutes": older_than_minutes, "updated": updated}
        except Exception as exc:
            return {"accepted": False, "action": "recover_stale_claimed", "server_name": server_name, "limit": limit, "older_than_minutes": older_than_minutes, "reason": str(exc), "updated": 0}

    def render_html(self, limit: int = 30, status: str | None = None, server_name: str | None = None) -> str:
        return render_spawn_queue(self.summary(limit, status, server_name))

    def _summary(self, enabled: bool, reason: str, status: str | None, server_name: str | None, counts: dict[str, int] | None = None, total: int = 0, attention: int = 0, rows: list | None = None, hint: str = "") -> dict:
        if not enabled and not hint:
            hint = "Set DB_BRIDGE_BACKEND=mysql and configure DB_BRIDGE_MYSQL_DSN."
        return {"enabled": enabled, "reason": reason, "operator_hint": hint, "status_filter": status, "server_name_filter": server_name, "counts": counts or self._empty_counts(), "total": total, "needs_attention": attention, "recent": rows or []}

    def _counts(self, cur, server_name: str | None) -> dict[str, int]:
        sql = "SELECT status, COUNT(*) AS cnt FROM %s" % Table.SPAWN
        params: list = []
        if server_name:
            sql += " WHERE server_name = %s"
            params.append(server_name)
        sql += " GROUP BY status ORDER BY status"
        cur.execute(sql, tuple(params))
        counts = self._empty_counts()
        counts.update({str(row["status"]): int(row["cnt"] or 0) for row in cur.fetchall()})
        return counts

    def _rows(self, cur, limit: int, status: str | None, server_name: str | None) -> list:
        fields = "uid, request_id, server_name, agent_id, name, class_type, level, loc_x, loc_y, loc_map, priority, status, attempts, last_error, created_at, claimed_at, done_at"
        sql = "SELECT %s FROM %s" % (fields, Table.SPAWN)
        where: list[str] = []
        params: list = []
        if status:
            where.append("status = %s")
            params.append(status)
        if server_name:
            where.append("server_name = %s")
            params.append(server_name)
        if where:
            sql += " WHERE " + " AND ".join(where)
        params.append(limit)
        cur.execute(sql + " ORDER BY uid DESC LIMIT %s", tuple(params))
        return list(cur.fetchall())

    def _reset(self, from_status: str, message: str, server_name: str, limit: int) -> dict:
        limit = max(1, min(int(limit or 50), 500))
        server_name = self._clean_server(server_name)
        if settings.db_bridge_backend.lower() != "mysql":
            return {"accepted": False, "action": message, "server_name": server_name, "limit": limit, "from_status": from_status, "reason": "db_bridge_backend_not_mysql", "updated": 0}
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE %s SET status = %%s, claimed_at = NULL, done_at = NULL, last_error = %%s WHERE status = %%s AND server_name = %%s ORDER BY uid ASC LIMIT %%s" % Table.SPAWN, (SpawnStatus.PENDING, message, from_status, server_name, limit))
                    updated = int(cur.rowcount or 0)
            return {"accepted": True, "action": message, "server_name": server_name, "limit": limit, "from_status": from_status, "updated": updated}
        except Exception as exc:
            return {"accepted": False, "action": message, "server_name": server_name, "limit": limit, "from_status": from_status, "reason": str(exc), "updated": 0}

    def _empty_counts(self) -> dict[str, int]:
        return {status: 0 for status in SpawnStatus.ALL}

    def _clean_status(self, status: str | None) -> str | None:
        value = str(status or "").strip().lower()
        return value if value in SpawnStatus.SET else None

    def _clean_optional_server(self, server_name: str | None) -> str | None:
        value = str(server_name or "").strip()
        return self._clean_server(value) if value else None

    def _clean_server(self, server_name: str | None) -> str:
        value = str(server_name or "main").strip()
        safe = "".join(ch for ch in value if ch.isalnum() or ch in {"_", "-", "."})
        return safe[:64] or "main"


spawn_request_dashboard_service = SpawnRequestDashboardService()

__all__ = ["SpawnRequestDashboardService", "spawn_request_dashboard_service"]
