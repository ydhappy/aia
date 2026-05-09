from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_robot_spawn_request_api_falls_back_without_mysql() -> None:
    response = client.post(
        "/robot/spawn-requests",
        json={
            "server_name": "main",
            "count": 3,
            "classes": ["knight", "elf"],
            "level_min": 1,
            "level_max": 10,
            "metadata": {"memo": "API 생성 테스트"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "accepted" in data
    assert "created" in data
    assert "requests" in data


def test_robot_spawn_request_api_validates_count_limit() -> None:
    response = client.post(
        "/robot/spawn-requests",
        json={"server_name": "main", "count": 0},
    )
    assert response.status_code == 422
