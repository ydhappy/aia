from __future__ import annotations

from html import escape


STATUS_ORDER = ["pending", "claimed", "done", "failed"]


def render_spawn_queue_html(data: dict) -> str:
    counts = data.get("counts", {}) or _empty_counts()
    rows = data.get("recent", []) or []
    status_filter = data.get("status_filter") or "all"
    total = int(data.get("total", 0) or 0)
    needs_attention = int(data.get("needs_attention", 0) or 0)
    enabled = bool(data.get("enabled"))
    reason = escape(str(data.get("reason", "")))
    operator_hint = escape(str(data.get("operator_hint", "")))
    cards = _render_status_cards(counts)
    body_rows = "\n".join(_render_row(row) for row in rows) or "<tr><td colspan='13'>spawn request rows 없음</td></tr>"
    status_label = escape(str(status_filter))
    banner_class = "ok" if enabled and needs_attention == 0 else "warn"
    banner_text = "정상" if enabled and needs_attention == 0 else "확인 필요"

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AIA Robot Spawn Queue</title>
  <style>{_STYLE}</style>
</head>
<body>
<main>
  <h1>AIA Robot Spawn Queue</h1>
  <p class="sub">AIA가 적재한 로봇 생성 요청과 게임서버 poll/spawn 처리 상태를 확인합니다.</p>
  <section class="banner {banner_class}">
    <span class="badge">{escape(banner_text)}</span>
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
  {_render_actions()}
  <table>
    <thead>
      <tr>
        <th>uid</th><th>request</th><th>server</th><th>agent</th><th>name</th><th>class</th><th>level</th>
        <th>x/y/map</th><th>priority</th><th>status</th><th>try</th><th>created</th><th>message</th>
      </tr>
    </thead>
    <tbody>{body_rows}</tbody>
  </table>
  <p class="sub">적용: <code>sql/aia_robot_spawn_request_mysql55.sql</code> → <code>POST /robot/spawn-requests</code> → 게임서버 <code>AiaRobotSpawnPoller.runOnce()</code></p>
</main>
<script>{_SCRIPT}</script>
</body>
</html>"""


def _render_actions() -> str:
    return """
  <section class="actions">
    <div class="box">
      <b>failed 재시도</b>
      <label>server <input id="retryServer" value="main"></label>
      <label>limit <input id="retryLimit" value="50"></label>
      <button type="button" onclick="postAction('/dashboard/robot-spawn-queue/retry-failed','retryServer','retryLimit')">retry</button>
    </div>
    <div class="box">
      <b>claimed 복구</b>
      <label>server <input id="recoverServer" value="main"></label>
      <label>min <input id="recoverMinutes" value="10"></label>
      <label>limit <input id="recoverLimit" value="50"></label>
      <button type="button" onclick="recoverClaimed()">recover</button>
    </div>
  </section>"""


def _render_status_cards(counts: dict) -> str:
    return "".join(
        "<a class='card' href='?status={status}'><div>{status}</div><b>{count}</b></a>".format(
            status=escape(status),
            count=escape(str(int(counts.get(status, 0) or 0))),
        )
        for status in STATUS_ORDER
    )


def _render_row(row: dict) -> str:
    status = str(row.get("status", "pending") or "pending").strip().lower()
    if status not in STATUS_ORDER:
        status = "pending"
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


def _empty_counts() -> dict[str, int]:
    return {status: 0 for status in STATUS_ORDER}


_STYLE = """
body { margin:0; font-family:'Noto Sans KR', Arial, sans-serif; background:#101820; color:#eef6f7; }
main { max-width:1280px; margin:0 auto; padding:28px 18px 50px; }
h1 { margin:0 0 8px; font-size:32px; }
a { color:inherit; text-decoration:none; }
.sub { color:#9db2b8; margin:0 0 22px; }
.banner { display:flex; gap:12px; flex-wrap:wrap; align-items:center; border-radius:16px; padding:14px 16px; margin:18px 0; border:1px solid #385868; background:#172631; }
.banner.ok { border-color:#2c7a57; }
.banner.warn { border-color:#b26a2c; }
.badge { border-radius:999px; padding:7px 11px; background:#0a1117; font-weight:700; }
.toolbar { display:flex; gap:10px; flex-wrap:wrap; margin:14px 0 18px; }
.pill, button { background:#213745; border:1px solid #385868; border-radius:999px; padding:8px 12px; color:#d8f0f4; cursor:pointer; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:20px 0; }
.card { background:#182630; border:1px solid #2c4654; border-radius:14px; padding:16px; }
.card b { display:block; margin-top:6px; font-size:28px; }
.actions { display:flex; gap:10px; flex-wrap:wrap; margin:16px 0 24px; }
.actions .box { display:flex; gap:8px; align-items:center; flex-wrap:wrap; background:#14222b; border:1px solid #2c4654; border-radius:14px; padding:10px; }
input { background:#0a1117; color:#eef6f7; border:1px solid #385868; border-radius:8px; padding:7px; width:76px; }
table { width:100%; border-collapse:collapse; background:#14222b; border-radius:12px; overflow:hidden; }
th,td { border-bottom:1px solid #2c4654; padding:9px; text-align:left; vertical-align:top; font-size:13px; }
th { background:#203643; color:#cfe9ef; }
.pending { color:#ffd166; font-weight:700; }
.claimed { color:#8ecae6; font-weight:700; }
.done { color:#80ed99; font-weight:700; }
.failed { color:#ff6b6b; font-weight:700; }
.warn-text { color:#ffb703; }
code { background:#0a1117; padding:2px 5px; border-radius:6px; }
"""


_SCRIPT = """
function enc(id) { return encodeURIComponent(document.getElementById(id).value || ''); }
function postAction(path, serverId, limitId) {
  fetch(path + '?server_name=' + enc(serverId) + '&limit=' + enc(limitId), { method:'POST' })
    .then(r => r.json())
    .then(j => { alert(JSON.stringify(j)); location.reload(); })
    .catch(e => alert('request failed: ' + e));
}
function recoverClaimed() {
  fetch('/dashboard/robot-spawn-queue/recover-claimed?server_name=' + enc('recoverServer') + '&older_than_minutes=' + enc('recoverMinutes') + '&limit=' + enc('recoverLimit'), { method:'POST' })
    .then(r => r.json())
    .then(j => { alert(JSON.stringify(j)); location.reload(); })
    .catch(e => alert('request failed: ' + e));
}
"""
