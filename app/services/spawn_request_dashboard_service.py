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
STATUS_ORDER = ["pending", "claimed", "done", "failed"]


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
            counts = self._empty_counts()
            return {
                "enabled": False,
                "reason": "db_bridge_backend_not_mysql",
                "operator_hint": "Set DB_BRIDGE_BACKEND=mysql and configure DB_BRIDGE_MYSQL_DSN.",
                "status_filter": status,
                "counts": counts,
                "total": 0,
                "needs_attention": 0,
                "recent": [],
            }
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT status, COUNT(*) AS cnt "
                        "FROM aia_robot_spawn_request GROUP BY status ORDER BY status"
                    )
                    counts = self._empty_counts()
                    counts.update({str(row["status"]): int(row["cnt"] or 0) for row in cur.fetchall()})
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
            total = sum(counts.values())
            needs_attention = counts.get("failed", 0) + counts.get("claimed", 0)
            return {
                "enabled": True,
                "reason": "",
                "operator_hint": "",
                "status_filter": status,
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
                "counts": counts,
                "total": 0,
                "needs_attention": 0,
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
        counts = data.get("counts", {}) or self._empty_counts()
        rows = data.get("recent", []) or []
        status_filter = data.get("status_filter") or "all"
        total = int(data.get("total", 0) or 0)
        needs_attention = int(data.get("needs_attention", 0) or 0)
        enabled = bool(data.get("enabled"))
        reason = escape(str(data.get("reason", "")))
        operator_hint = escape(str(data.get("operator_hint", "")))
        cards = self._render_status_cards(counts)
        body_rows = "\n".join(self._render_row(row) for row in rows) or "<tr><td colspan='13'>spawn request rows 없음</td></tr>"
        status_label = escape(str(status_filter))
        banner_class = "ok" if enabled and needs_attention == 0 else "warn"
        banner_text = "정상" if enabled and needs_attention == 0 else "확인 필요"
        return """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AIA Robot Spawn Queue</title>
  <style>
    body {{ margin:0; font-family:'Noto Sans KR', Arial, sans-serif; background:#101820; color:#eef6f7; }}
    main {{ max-width:1280px; margin:0 auto; padding:28px 18px 50px; }}
    h1 {{ margin:0 0 8px; font-size:32px; }}
    a {{ color:inherit; text-decoration:none; }}
    .sub {{ color:#9db2b8; margin:0 0 22px; }}
    .banner {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; border-radius:16px; padding:14px 16px; margin:18px 0; border:1px solid #385868; background:#172631; }}
    .banner.ok {{ border-color:#2c7a57; }}
    .banner.warn {{ border-color:#b26a2c; }}
    .badge {{ border-radius:999px; padding:7px 11px; background:#0a1117; font-weight:700; }}
    .toolbar {{ display:flex; gap:10px; flex-wrap:wrap; margin:14px 0 18px; }}
    .pill, button {{ background:#213745; border:1px solid #385868; border-radius:999px; padding:8px 12px; color:#d8f0f4; cursor:pointer; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:20px 0; }}
    .card {{ background:#182630; border:1px solid #2c4654; border-radius:14px; padding:16px; }}
    .card b {{ display:block; margin-top:6px; font-size:28px; }}
    .actions {{ display:flex; gap:10px; flex-wrap:wrap; margin:16px 0 24px; }}
    .actions form {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; background:#14222b; border:1px solid #2c4654; border-radius:14px; padding:10px; }}
    input {{ background:#0a1117; color:#eef6f7; border:1px solid #385868; border-radius:8px; padding:7px; width:76px; }}
    table {{ width:100%; border-collapse:collapse; background:#14222b; border-radius:12px; overflow:hidden; }}
    th,td {{ border-bottom:1px solid #2c4654; padding:9px; text-align:left; vertical-align:top; font-size:13px; }}
    th {{ background:#203643; color:#cfe9ef; }}
    .pending {{ color:#ffd166; font-weight:700; }}
    .claimed {{ color:#8ecae6; font-weight:700; }}
    .done {{ color:#80ed99; font-weight:700; }}
    .failed {{ color:#ff6b6b; font-weight:700; }}
    .warn-text {{ color:#ffb703; }}
    code {{ background:#0a1117; padding:2px 5px; border-radius:6px; }}
  </style>
</head>
<body>
<main>
  <h1>AIA Robot Spawn Queue</h1>
  <p class="sub">AIA가 적재한 로봇 생성 요청과 게임서버 poll/spawn 처리 상태를 확인합니다.</p>
  <section class="banner {banner_class}">
    <span class="badge">{banner_text}</span>
    <span>total={total}</span>
    <span>needs_attention={needs_attention}</span>
    <span>현재 필터={status_label}</span>
  </section>
  <div class="toolbar">
    <a class="pill" href="?">전체</a>
    <a class="pill" href="?status=pending">pending</a>
    <a class="pill" href="?status=claimed">claimed</a>
    <a class="pill" href="?status=done">done</a>
    <a class="pill" href="?status=failed">failed</a>
  </div>
  <p class="warn-text">{reason}</p>
  <p class="sub">{operator_hint}</p>
  <section class="cards">{cards}</section>
  <section class="actions">
    <form method="post" action="/dashboard/robot-spawn-queue/retry-failed">
      <b>failed 재시도</b><label>server <input name="server_name" value="main"></label><label>limit <input name="limit" value="50"></label><button type="submit">retry</button>
    </form>
    <form method="post" action="/dashboard/robot-spawn-queue/recover-claimed">
      <b>claimed 복구</b><label>server <input name="server_name" value="main"></label><label>min <input name="older_than_minutes" value="10"></label><label>limit <input name="limit" value="50"></label><button type="submit">recover</button>
    </form>
  </section>
  <table>
    <thead><tr><th>uid</th><th>request</th><th>server</th><th>agent</th><th>name</th><th>class</th><th>level</th><th>x/y/map</th><th>priority</th><th>status</th><th>try</th><th>created</th><th>message</th></tr></thead>
    <tbody>{body_rows}</tbody>
  </table>
  <p class="sub">적용: <code>sql/aia_robot_spawn_request_mysql55.sql</code> → <code>POST /robot/spawn-requests</code> → 게임서버 <code>AiaRobotSpawnPoller.runOnce()</code></p>
</main>
</body>
</html>""".format(
            banner_class=banner_class,
            banner_text=escape(banner_text),
            total=total,
            needs_attention=needs_attention,
            status_label=status_label,
            reason=reason,
            operator_hint=operator_hint,
            cards=cards,
            body_rows=body_rows,
        )

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

    def _render_status_cards(self, counts: dict) -> str:
        return "".join(
            "<a class='card' href='?status={status}'><div>{status}</div><b>{count}</b></a>".format(
                status=escape(status), count=escape(str(int(counts.get(status, 0) or 0)))
            )
            for status in STATUS_ORDER
        )

    def _render_row(self, row: dict) -> str:
        status = self._clean_status(str(row.get("status", ""))) or "pending"
        return (
            "<tr>"
            "<td>{uid}</td><td>{request}</td><td>{server}</td><td>{agent}</td><td>{name}</td><td>{clazz}</td>"
            "<td>{level}</td><td>{loc}</td><td>{priority}</td><td class='{status_class}'>{status}</td>"
            "<td>{attempts}</td><td>{created}</td><td>{error}</td>"
            "</tr>"
        ).format(
            uid=escape(str(row.get("uid", ""))),
            request=escape(str(row.get("request_id", ""))),
            server=escape(str(row.get("server_name", ""))),
            agent=escape(str(row.get("agent_id", ""))),
            name=escape(str(row.get("name", ""))),
            clazz=escape(str(row.get("class_type", ""))),
            level=escape(str(row.get("level", ""))),
            loc=escape("{}/{}/{}".format(row.get("loc_x", ""), row.get("loc_y", ""), row.get("loc_map", ""))),
            priority=escape(str(row.get("priority", ""))),
            status_class=escape(status),
            status=escape(status),
            attempts=escape(str(row.get("attempts", ""))),
            created=escape(str(row.get("created_at", ""))),
            error=escape(str(row.get("last_error", ""))),
        )

    def _empty_counts(self) -> dict[str, int]:
        return {status: 0 for status in STATUS_ORDER}

    def _clean_status(self, status: str | None) -> str | None:
        value = str(status or "").strip().lower()
        return value if value in VALID_STATUSES else None

    def _clean_server(self, server_name: str | None) -> str:
        value = str(server_name or "main").strip()
        return value[:64] or "main"


spawn_request_dashboard_service = SpawnRequestDashboardService()
