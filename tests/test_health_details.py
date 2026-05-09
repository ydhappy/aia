from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


REQUIRED_TABLES = {
    "aia_robot_spawn_request": "sql/aia_robot_spawn_request_mysql55.sql",
    "aia_robot_state": "sql/aia_robot_schema.sql",
    "aia_robot_event": "sql/aia_robot_schema.sql",
    "aia_robot_feedback": "sql/aia_robot_schema.sql",
    "aia_robot_decision": "sql/aia_robot_schema.sql",
    "aia_robot_trace_summary": "sql/aia_robot_schema.sql",
}


def test_health_details_includes_optional_mysql_status_and_security() -> None:
    response = client.get("/health/details")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "security" in data
    assert "api_key_auth_enabled" in data["security"]
    assert "bind_host" in data["security"]
    assert "warnings" in data["security"]
    assert "db_bridge_backend" in data
    assert "mysql" in data
    assert "enabled" in data["mysql"]
    assert "status" in data["mysql"]
    assert "tables" in data["mysql"]
    if data["mysql"].get("enabled"):
        assert "missing_tables" in data["mysql"]
        for table_name, required_sql in REQUIRED_TABLES.items():
            table = data["mysql"]["tables"].get(table_name)
            assert table is not None
            assert "exists" in table
            assert table["required_sql"] == required_sql
