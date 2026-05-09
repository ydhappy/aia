from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_details_includes_optional_mysql_status() -> None:
    response = client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_bridge_backend" in data
    assert "mysql" in data
    assert "enabled" in data["mysql"]
    assert "status" in data["mysql"]
