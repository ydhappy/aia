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


def test_spawn_request_dashboard_gui_renders_without_mysql() -> None:
    response = client.get("/dashboard/robot-spawn-queue/gui")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AIA Robot Spawn Queue" in response.text
