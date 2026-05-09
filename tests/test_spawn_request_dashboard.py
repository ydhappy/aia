from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_spawn_request_dashboard_json_falls_back_without_mysql() -> None:
    response = client.get("/dashboard/robot-spawn-queue")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "counts" in data
    assert "recent" in data


def test_spawn_request_dashboard_json_accepts_status_filter() -> None:
    response = client.get("/dashboard/robot-spawn-queue?status=failed")
    assert response.status_code == 200
    data = response.json()
    assert "status_filter" in data
    assert "counts" in data
    assert "recent" in data


def test_spawn_request_dashboard_gui_renders_without_mysql() -> None:
    response = client.get("/dashboard/robot-spawn-queue/gui?status=failed")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AIA Robot Spawn Queue" in response.text
    assert "현재 필터" in response.text


def test_spawn_request_retry_failed_falls_back_without_mysql() -> None:
    response = client.post("/dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "accepted" in data
    assert "updated" in data


def test_spawn_request_recover_claimed_falls_back_without_mysql() -> None:
    response = client.post("/dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "accepted" in data
    assert "updated" in data
