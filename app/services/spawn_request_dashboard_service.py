from __future__ import annotations

from datetime import datetime, timedelta
from html import escape
from urllib.parse import urlparse

from app.core.config import settings

try:
    import pymysql
except Exception:  # pragma: no cover
    pymysql = None


VALID_STATUSES = {"pending", "claimed", "done", "failed"}


class SpawnRequestDashboardService:
    def _connect(self):
        if pymysql is None:
            raise RuntimeError("pymysql_not_installed")
        parsed = urlparse(settings.db_bridge_mysql_dsn.replace("mysql+pymysql://", "mysql://"))
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

    def summary(self, limit: int = 30, status: str | None = None) -> dict:
        limit = max(1, min(int(limit or 30), 200))
        status = self._clean_status(status)
        if settings.db_bridge_backend.lower() != "mysql":
            return {
                "enabled": False,
                "reason": "db_bridge_backend_not_mysql",
                "status_filter": status,
                "counts": {},
                "recent": [],
            }
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT status, COUNT(*) AS cnt "
                        "FROM aia_robot_spawn_request GROUP BY status ORDER BY status"
                    )
                    counts = {str(row["status"]): int(row["cnt"] or 0) for row in cur.fetchall()}
                    base_sql = (
                        "SELECT uid, request_id, server_name, agent_id, name, class_type, level, "
                        "loc_x, loc_y, loc_map, priority, status, attempts, last_error, created_at, claimed_at, done_at "
                        "FROM aia_robot_spawn_request"
                    )
                    if status:
                        cur.execute(base_sql + " WHERE status = %s ORDER BY uid DESC LIMIT %s", (status, limit))
                    else:
                        cur.execute(base_sql + " ORDER BY uid DESC LIMIT %s", (limit,))
                    rows = list(cur.fetchall())
            return {
                "enabled": True,
                "status_filter": status,
                "counts": counts,
                "recent": rows,
            }
        except Exception as exc:
            return {
                "enabled": False,
                "reason": str(exc),
                "status_filter": status,
                "counts": {},
                "recent": [],
            }

    def retry_failed(self, server_name: str = "main", limit: int = 50) -> dict:
        return self._reset_status(
            from_status="failed",
            message="retry_failed",
            server_name=server_name,
            limit=limit,
        )

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

    def render_html(self, limit: int = 30, status: str | None = None) -> str:
        data = self.summary(limit, status)
        counts = data.get("counts", {}) or {}
        rows = data.get("recent", []) or []
        status_filter = data.get("status_filter") or "all"
        cards = "".join(
            "<a class='card' href='?status={}'><div>{}</div><b>{}</b></a>".format(
                escape(str(key)), escape(str(key)), escape(str(value))
            )
            for key, value in counts.items()
        ) or "<div class='card'><div>status</div><b>no data</b></div>"
        body_rows = "\n".join(
            "<tr>"
            "<td>{uid}</td><td>{server}</td><td>{agent}</td><td>{name}</td><td>{clazz}</td>"
            "<td>{level}</td><td>{loc}</td><td class='{status_class}'>{status}</td>"
            "<td>{attempts}</td><td>{error}</td>"
            "</tr>".format(
                uid=escape(str(row.get("uid", ""))),
                server=escape(str(row.get("server_name", ""))),
                agent=escape(str(row.get("agent_id", ""))),
                name=escape(str(row.get("name", ""))),
                clazz=escape(str(row.get("class_type", ""))),
                level=escape(str(row.get("level", ""))),
                loc=escape("{}/{}/{}".format(row.get("loc_x", ""), row.get("loc_y", ""), row.get("loc_map", ""))),
                status_class=escape(str(row.get("status", ""))),
                status=escape(str(row.get("status", ""))),
                attempts=escape(str(row.get("attempts", ""))),
                error=escape(str(row.get("last_error", ""))),
            )
            for row in rows
        ) or "<tr><td colspan='10'>spawn request rows 없음</td></tr>"
        reason = escape(str(data.get("reason", "")))
        return """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AIA Robot Spawn Queue</title>
  <style>
    body {{ margin:0; font-family:'Noto Sans KR', Arial, sans-serif; background:#101820; color:#eef6f7; }}
    main {{ max-width:1180px; margin:0 auto; padding:28px 18px 50px; }}
    h1 {{ margin:0 0 8px; font-size:32px; }}
    a {{ color:inherit; text-decoration:none; }}
    .sub {{ color:#9db2b8; margin:0 0 22px; }}
    .toolbar {{ display:flex; gap:10px; flex-wrap:wrap; margin:14px 0 18px; }}
    .pill {{ background:#213745; border:1px solid #385868; border-radius:999px; padding:8px 12px; color:#d8f0f4; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:20px 0; }}
    .card {{ background:#182630; border:1px solid #2c4654; border-radius:14px; padding:16px; }}
    .card b {{ display:block; margin-top:6px; font-size:28px; }}
    table {{ width:100%; border-collapse:collapse; background:#14222b; border-radius:12px; overflow:hidden; }}
    th,td {{ border-bottom:1px solid #2c4654; padding:10px; text-align:left; vertical-align:top; }}
    th {{ background:#203643; color:#cfe9ef; }}
    .pending {{ color:#ffd166; font-weight:700; }}
    .claimed {{ color:#8ecae6; font-weight:700; }}
    .done {{ color:#80ed99; font-weight:700; }}
    .failed {{ color:#ff6b6b; font-weight:700; }}
    .warn {{ color:#ffb703; }}
    code {{ background:#0a1117; padding:2px 5px; border-radius:6px; }}
  </style>
</head>
<body>
<main>
  <h1>AIA Robot Spawn Queue</h1>
  <p class="sub">AIA가 적재한 로봇 생성 요청과 게임서버 poll/spawn 처리 상태를 확인합니다.</p>
  <div class="toolbar">
    <a class="pill" href="?">전체</a>
    <a class="pill" href="?status=pending">pending</a>
    <a class="pill" href="?status=claimed">claimed</a>
    <a class="pill" href="?status=done">done</a>
    <a class="pill" href="?status=failed">failed</a>
    <span class="pill">현재 필터: {status_filter}</span>
  </div>
  <p class="warn">{reason}</p>
  <section class="cards">{cards}</section>
  <table>
    <thead><tr><th>uid</th><th>server</th><th>agent</th><th>name</th><th>class</th><th>level</th><th>x/y/map</th><th>status</th><th>try</th><th>message</th></tr></thead>
    <tbody>{body_rows}</tbody>
  </table>
  <p class="sub">복구 API: <code>POST /dashboard/robot-spawn-queue/retry-failed</code>, <code>POST /dashboard/robot-spawn-queue/recover-claimed</code></p>
  <p class="sub">적용: <code>sql/aia_robot_spawn_request_mysql55.sql</code> → <code>POST /robot/spawn-requests</code> → 게임서버 <code>AiaRobotSpawnPoller.runOnce()</code></p>
</main>
</body>
</html>""".format(reason=reason, cards=cards, body_rows=body_rows, status_filter=escape(str(status_filter)))

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

    def _clean_status(self, status: str | None) -> str | None:
        value = str(status or "").strip().lower()
        return value if value in VALID_STATUSES else None

    def _clean_server(self, server_name: str | None) -> str:
        value = str(server_name or "main").strip()
        return value[:64] or "main"


spawn_request_dashboard_service = SpawnRequestDashboardService()
