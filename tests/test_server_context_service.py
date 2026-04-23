from app.services.robot_autonomy_baseline_service import robot_autonomy_baseline_service
from app.services.server_context_service import server_context_service


def test_server_context_detects_mysql_database_and_contract() -> None:
    snapshot = server_context_service.snapshot()

    assert snapshot["mysql"]["database"] == "sp163"
    assert snapshot["portable_contract"]["requires_robot_tables"] is False
    assert snapshot["robot_db_contract"] == ["robot", "robot_clan", "robot_setting"]
    assert "aia_robot_state" in snapshot["aia_db_contract"]
    assert snapshot["world_guides"]["enabled"] is True
    assert snapshot["world_guides"]["hunt_zone_count"] > 0
    assert snapshot["world_guides"]["siege_guide_count"] >= 1


def test_autonomy_operator_view_includes_server_context() -> None:
    view = robot_autonomy_baseline_service.operator_view()

    assert view["server_context"]["server_id"] == "sp163"
    assert view["server_context"]["portable_contract"]["server_version_agnostic"] is True
    assert view["summary"]["aia_db_hunt_zones"] > 0
