from __future__ import annotations

from html import escape
from urllib.parse import urlparse

from app.core.config import settings

try:
    import pymysql
except Exception:  # pragma: no cover
    pymysql = None


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

    def summary(self, limit: int = 30) -> dict:
        limit = max(1, min(int(limit or 30), 200))
        if settings.db_bridge_backend.lower() != "mysql":
            return {
                "enabled": False,
                "reason": "db_bridge_backend_not_mysql",
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
                    cur.execute(
                        "SELECT uid, request_id, server_name, agent_id, name, class_type, level, "
                        "loc_x, loc_y, loc_map, priority, status, attempts, last_error, created_at, claimed_at, done_at "
                        "FROM aia_robot_spawn_request ORDER BY uid DESC LIMIT %s",
                        (limit,),
                    )
                    rows = list(cur.fetchall())
            return {
                "enabled": True,
                "counts": counts,
                "recent": rows,
            }
        except Exception as exc:
            return {
                "enabled": False,
                "reason": str(exc),
                "counts": {},
                "recent": [],
            }

    def render_html(self, limit: int = 30) -> str:
        data = self.summary(limit)
        counts = data.get("counts", {}) or {}
        rows = data.get("recent", []) or []
        cards = "".join(
            "<div class='card'><div>{}</div><b>{}</b></div>".format(escape(str(key)), escape(str(value)))
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
    .sub {{ color:#9db2b8; margin:0 0 22px; }}
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
  <p class="warn">{reason}</p>
  <section class="cards">{cards}</section>
  <table>
    <thead><tr><th>uid</th><th>server</th><th>agent</th><th>name</th><th>class</th><th>level</th><th>x/y/map</th><th>status</th><th>try</th><th>message</th></tr></thead>
    <tbody>{body_rows}</tbody>
  </table>
  <p class="sub">적용: <code>sql/aia_robot_spawn_request_mysql55.sql</code> → <code>scripts/seed_robot_spawn_requests_mysql55.py</code> → 게임서버 <code>AiaRobotSpawnPoller.runOnce()</code></p>
</main>
</body>
</html>""".format(reason=reason, cards=cards, body_rows=body_rows)


spawn_request_dashboard_service = SpawnRequestDashboardService()
