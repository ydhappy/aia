from app.services.spawn_request_dashboard_renderer import render_spawn_queue_html


def test_spawn_queue_renderer_escapes_row_values_and_renders_actions() -> None:
    html = render_spawn_queue_html(
        {
            "enabled": True,
            "reason": "",
            "operator_hint": "",
            "status_filter": "failed",
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
    assert "failed 재시도" in html
    assert "claimed 복구" in html
    assert "recoverClaimed" in html
    assert "req&lt;script&gt;" in html
    assert "로봇&lt;script&gt;" in html
    assert "bad&lt;script&gt;" in html
    assert "req<script>" not in html
