from __future__ import annotations

from datetime import datetime, timedelta

from app.core.config import settings
from app.core.mysql import connect_mysql
from app.services.spawn_request_dashboard_renderer import STATUS_ORDER, render_spawn_queue_html


VALID_STATUSES = {"pending", "claimed", "done", "failed"}


class SpawnRequestDashboardService:
    def _connect(self):
        return connect_mysql(settings.db_bridge_mysql_dsn)

    def summary(self, limit: int = 30, status: str | None = None, server_name: str | None = None) -> dict:
        limit = max(1, min(int(limit or 30), 200))
        status = self._clean_status(status)
        server_name = self._clean_optional_server(server_name)
        if settings.db_bridge_backend.lower() != "mysql":
            counts = self._empty_counts()
            return {
                "enabled": False,
                "reason": "db_bridge_backend_not_mysql",
                "operator_hint": "Set DB_BRIDGE_BACKEND=mysql and configure DB_BRIDGE_MYSQL_DSN.",
                "status_filter": status,
                "server_name_filter": server_name,
                "counts": counts,
                "total": 0,
                "needs_attention": 0,
                "recent": [],
            }
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    count_sql = "SELECT status, COUNT(*) AS cnt FROM aia_robot_spawn_request"
                    count_params: list = []
                    if server_name:
                        count_sql += " WHERE server_name = %s"
                        count_params.append(server_name)
                    count_sql += " GROUP BY status ORDER BY status"
                    cur.execute(count_sql, tuple(count_params))
                    counts = self._empty_counts()
                    counts.update({str(row["status"]): int(row["cnt"] or 0) for row in cur.fetchall()})

                    base_sql = (
                        "SELECT uid, request_id, server_name, agent_id, name, class_type, level, "
                        "loc_x, loc_y, loc_map, priority, status, attempts, last_error, created_at, claimed_at, done_at "
                        "FROM aia_robot_spawn_request"
                    )
                    where_clauses = []
                    params: list = []
                    if status:
                        where_clauses.append("status = %s")
                        params.append(status)
                    if server_name:
                        where_clauses.append("server_name = %s")
                        params.append(server_name)
                    if where_clauses:
                        base_sql += " WHERE " + " AND ".join(where_clauses)
                    params.append(limit)
                    cur.execute(base_sql + " ORDER BY uid DESC LIMIT %s", tuple(params))
                    rows = list(cur.fetchall())
            total = sum(counts.values())
            needs_attention = counts.get("failed", 0) + counts.get("claimed", 0)
            return {
                "enabled": True,
                "reason": "",
                "operator_hint": "",
                "status_filter": status,
                "server_name_filter": server_name,
                "counts": counts,
                "total": total,
                "needs_attention": needs_attention,
                "recent": rows,
            }
        except Exception as exc:
            counts = self._empty_counts()
            return {
                "enabled": False,
                "reason": str(exc),
                "operator_hint": "Check MySQL connection, table sql/aia_robot_spawn_request_mysql55.sql, and DB user permissions.",
                "status_filter": status,
                "server_name_filter": server_name,
                "counts": counts,
                "total": 0,
                "needs_attention": 0,
                "recent": [],
            }

    def retry_failed(self, server_name: str = "main", limit: int = 50) -> dict:
        return self._reset_status("failed", "retry_failed", server_name, limit)

    def recover_stale_claimed(self, server_name: str = "main", older_than_minutes: int = 10, limit: int = 50) -> dict:
        limit = max(1, min(int(limit or 50), 500))
        older_than_minutes = max(1, min(int(older_than_minutes or 10), 1440))
        server_name = self._clean_server(server_name)
        if settings.db_bridge_backend.lower() != "mysql":
            return {
                "accepted": False,
                "action": "recover_stale_claimed",
                "server_name": server_name,
                "limit": limit,
                "older_than_minutes": older_than_minutes,
                "reason": "db_bridge_backend_not_mysql",
                "updated": 0,
            }
        cutoff = datetime.now() - timedelta(minutes=older_than_minutes)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE aia_robot_spawn_request "
                        "SET status = 'pending', claimed_at = NULL, last_error = 'recovered_stale_claimed' "
                        "WHERE status = 'claimed' AND server_name = %s AND claimed_at IS NOT NULL AND claimed_at < %s "
                        "ORDER BY uid ASC LIMIT %s",
                        (server_name, cutoff, limit),
                    )
                    updated = int(cur.rowcount or 0)
            return {
                "accepted": True,
                "action": "recover_stale_claimed",
                "server_name": server_name,
                "limit": limit,
                "older_than_minutes": older_than_minutes,
                "updated": updated,
            }
        except Exception as exc:
            return {
                "accepted": False,
                "action": "recover_stale_claimed",
                "server_name": server_name,
                "limit": limit,
                "older_than_minutes": older_than_minutes,
                "reason": str(exc),
                "updated": 0,
            }

    def render_html(self, limit: int = 30, status: str | None = None, server_name: str | None = None) -> str:
        return render_spawn_queue_html(self.summary(limit, status, server_name))

    def _reset_status(self, from_status: str, message: str, server_name: str, limit: int) -> dict:
        limit = max(1, min(int(limit or 50), 500))
        server_name = self._clean_server(server_name)
        if settings.db_bridge_backend.lower() != "mysql":
            return {
                "accepted": False,
                "action": message,
                "server_name": server_name,
                "limit": limit,
                "from_status": from_status,
                "reason": "db_bridge_backend_not_mysql",
                "updated": 0,
            }
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE aia_robot_spawn_request "
                        "SET status = 'pending', claimed_at = NULL, done_at = NULL, last_error = %s "
                        "WHERE status = %s AND server_name = %s ORDER BY uid ASC LIMIT %s",
                        (message, from_status, server_name, limit),
                    )
                    updated = int(cur.rowcount or 0)
            return {
                "accepted": True,
                "action": message,
                "server_name": server_name,
                "limit": limit,
                "from_status": from_status,
                "updated": updated,
            }
        except Exception as exc:
            return {
                "accepted": False,
                "action": message,
                "server_name": server_name,
                "limit": limit,
                "from_status": from_status,
                "reason": str(exc),
                "updated": 0,
            }

    def _empty_counts(self) -> dict[str, int]:
        return {status: 0 for status in STATUS_ORDER}

    def _clean_status(self, status: str | None) -> str | None:
        value = str(status or "").strip().lower()
        return value if value in VALID_STATUSES else None

    def _clean_optional_server(self, server_name: str | None) -> str | None:
        value = str(server_name or "").strip()
        if not value:
            return None
        return self._clean_server(value)

    def _clean_server(self, server_name: str | None) -> str:
        value = str(server_name or "main").strip()
        safe = "".join(ch for ch in value if ch.isalnum() or ch in {"_", "-", "."})
        return safe[:64] or "main"


spawn_request_dashboard_service = SpawnRequestDashboardService()
