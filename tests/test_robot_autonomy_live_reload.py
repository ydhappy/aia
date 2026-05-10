from pathlib import Path

from app.services.autonomy import RobotAutonomyBaselineService


def test_robot_autonomy_service_uses_live_json_files(tmp_path: Path) -> None:
    service = RobotAutonomyBaselineService()
    service.config_path = tmp_path / "robot_autonomy_defaults.json"
    service.top_profile_path = tmp_path / "aia_robot_top_profile.json"
    service.config_file.path = service.config_path
    service.top_profile_file.path = service.top_profile_path

    service.config_path.write_text(
        '{"version": 1, "defaults": {"style": "balanced"}, "class_profiles": {"default": {"role": "dealer"}}, "hunt_zones": [], "talk_templates": {"hunt": ["first"]}}\n',
        encoding="utf-8",
    )
    assert service.load()["version"] == 1

    service.config_path.write_text(
        '{"version": 2, "defaults": {"style": "defensive"}, "class_profiles": {"default": {"role": "tank"}}, "hunt_zones": [], "talk_templates": {"hunt": ["second"]}}\n',
        encoding="utf-8",
    )
    assert service.load()["version"] == 2

    service.top_profile_path.write_text('{"behavior_constants": {"roam": 1}}\n', encoding="utf-8")
    view = service.operator_view()
    assert view["live_reload"]["enabled"] is True
    assert view["live_reload"]["config"]["live_reload"] is True
    assert view["live_reload"]["top_profile"]["live_reload"] is True
    assert view["aia_top_profile"]["behavior_constants"] == {"roam": 1}
