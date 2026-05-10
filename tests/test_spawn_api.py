from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_spawn_api_fallback_without_mysql() -> None:
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


def test_spawn_api_validates_count_limit() -> None:
    response = client.post("/robot/spawn-requests", json={"server_name": "main", "count": 0})
    assert response.status_code == 422


def test_spawn_api_validates_level_range() -> None:
    response = client.post("/robot/spawn-requests", json={"server_name": "main", "level_min": 30, "level_max": 10})
    assert response.status_code == 422


def test_spawn_api_validates_classes_not_empty() -> None:
    response = client.post("/robot/spawn-requests", json={"server_name": "main", "classes": []})
    assert response.status_code == 422
