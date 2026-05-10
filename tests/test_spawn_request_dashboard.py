from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_spawn_request_dashboard_json_falls_back_without_mysql() -> None:
    response = client.get("/dashboard/robot-spawn-queue")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "counts" in data
    assert "total" in data
    assert "needs_attention" in data
    assert "operator_hint" in data
    assert "server_name_filter" in data
    assert "recent" in data


def test_spawn_request_dashboard_json_accepts_status_and_server_filters() -> None:
    response = client.get("/dashboard/robot-spawn-queue?status=failed&server_name=main")
    assert response.status_code == 200
    data = response.json()
    assert data["status_filter"] == "failed"
    assert data["server_name_filter"] == "main"
    assert "counts" in data
    assert "recent" in data


def test_spawn_request_dashboard_gui_renders_without_mysql() -> None:
    response = client.get("/dashboard/robot-spawn-queue/gui?status=failed&server_name=main")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AIA Robot Spawn Queue" in response.text
    assert "needs_attention" in response.text
    assert "현재 서버 필터=main" in response.text
    assert "서버 필터" in response.text
    assert "failed 재시도" in response.text
    assert "claimed 복구" in response.text
    assert "postAction" in response.text
    assert "recoverClaimed" in response.text
    assert "applyServerFilter" in response.text


def test_spawn_request_retry_failed_falls_back_without_mysql() -> None:
    response = client.post("/dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "retry_failed"
    assert data["server_name"] == "main"
    assert data["limit"] == 5
    assert "accepted" in data
    assert "updated" in data


def test_spawn_request_recover_claimed_falls_back_without_mysql() -> None:
    response = client.post("/dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "recover_stale_claimed"
    assert data["server_name"] == "main"
    assert data["limit"] == 5
    assert data["older_than_minutes"] == 10
    assert "accepted" in data
    assert "updated" in data
