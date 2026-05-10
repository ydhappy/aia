from app.ui.spawn_queue import render_spawn_queue


def test_spawn_ui_escapes_values_and_renders_actions() -> None:
    html = render_spawn_queue(
        {
            "enabled": True,
            "reason": "",
            "operator_hint": "",
            "status_filter": "failed",
            "server_name_filter": "main",
            "counts": {"pending": 1, "claimed": 2, "done": 3, "failed": 4},
            "total": 10,
            "needs_attention": 6,
            "recent": [
                {
                    "uid": 1,
                    "request_id": "req<script>",
                    "server_name": "main",
                    "agent_id": "agent-1",
                    "name": "로봇<script>",
                    "class_type": "knight",
                    "level": 10,
                    "loc_x": 1,
                    "loc_y": 2,
                    "loc_map": 3,
                    "priority": 100,
                    "status": "failed",
                    "attempts": 1,
                    "created_at": "now",
                    "last_error": "bad<script>",
                }
            ],
        }
    )
    assert "AIA Robot Spawn Queue" in html
    assert "needs_attention=6" in html
    assert "현재 서버 필터=main" in html
    assert "server_name=main" in html
    assert "서버 필터" in html
    assert "failed 재시도" in html
    assert "claimed 복구" in html
    assert "recoverClaimed" in html
    assert "applyServerFilter" in html
    assert "req&lt;script&gt;" in html
    assert "로봇&lt;script&gt;" in html
    assert "bad&lt;script&gt;" in html
    assert "req<script>" not in html
