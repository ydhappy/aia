def test_short_service_modules_import() -> None:
    from app.services.autonomy import RobotAutonomyBaselineService, robot_autonomy_baseline_service
    from app.services.spawn import RobotSpawnRequestService, robot_spawn_request_service
    from app.services.spawn_dash import SpawnRequestDashboardService, spawn_request_dashboard_service

    assert RobotAutonomyBaselineService is not None
    assert robot_autonomy_baseline_service is not None
    assert RobotSpawnRequestService is not None
    assert robot_spawn_request_service is not None
    assert SpawnRequestDashboardService is not None
    assert spawn_request_dashboard_service is not None
