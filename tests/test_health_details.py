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
    assert "tables" in data["mysql"]
    if data["mysql"].get("enabled"):
        table = data["mysql"]["tables"].get("aia_robot_spawn_request")
        assert table is not None
        assert "exists" in table
        assert table["required_sql"] == "sql/aia_robot_spawn_request_mysql55.sql"
