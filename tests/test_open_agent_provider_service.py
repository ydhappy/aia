from app.services.open_agent_provider_service import open_agent_provider_service


def test_open_agent_provider_registry_contains_safe_sidecars() -> None:
    providers = open_agent_provider_service.providers()
    keys = {provider["key"] for provider in providers}
    assert {"native", "ollama_openai", "langgraph", "microsoft_agent_framework", "crewai", "autogen"} <= keys
    assert any(provider["configured"] for provider in providers)


def test_open_agent_absorption_plan_keeps_aia_as_final_policy_layer() -> None:
    plan = open_agent_provider_service.absorption_plan()
    assert plan["mode"] == "aia_native_core_with_optional_sidecars"
    assert plan["do_not_vendor_by_default"] is True
    assert "AIA_policy_engine_remains_final_decision_layer" in plan["safety_rules"]
    assert "game_server_remains_final_execution_validator" in plan["safety_rules"]
