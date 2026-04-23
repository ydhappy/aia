from __future__ import annotations

from typing import Any

from app.core.config import settings


class OpenAgentProviderService:
    """Registry for optional open-source agent runtimes.

    AIA keeps the game-critical robot loop native and deterministic. External
    frameworks are absorbed as sidecars so their licenses, dependencies, and
    latency cannot destabilize the game server.
    """

    def providers(self) -> list[dict[str, Any]]:
        configured = settings.agent_framework_provider.lower()
        return [
            self._provider(
                key="native",
                name="AIA Native Autonomy Core",
                role="required_core",
                license_note="project-native",
                integration_mode="in_process",
                strengths=["low_latency", "deterministic_policy", "robot_ops_tick"],
                recommended=True,
                configured=configured == "native",
            ),
            self._provider(
                key="ollama_openai",
                name="Ollama OpenAI-Compatible Runtime",
                role="local_llm_sidecar",
                license_note="model-dependent",
                integration_mode="openai_compatible_http",
                strengths=["local_models", "no_external_api_required", "chat_completions"],
                recommended=True,
                configured=settings.llm_backend.lower() in {"ollama", "self_hosted"} and settings.llm_base_url,
            ),
            self._provider(
                key="langgraph",
                name="LangGraph",
                role="agent_orchestration_sidecar",
                license_note="MIT according to official LangGraph materials",
                integration_mode="sidecar_http_or_queue",
                strengths=["stateful_graphs", "checkpointing", "long_running_workflows"],
                recommended=True,
                configured=configured == "langgraph",
            ),
            self._provider(
                key="microsoft_agent_framework",
                name="Microsoft Agent Framework",
                role="enterprise_multi_agent_sidecar",
                license_note="verify before vendoring; prefer sidecar",
                integration_mode="sidecar_http_or_mcp",
                strengths=["multi_agent_orchestration", "cross_runtime", "enterprise_support"],
                recommended=True,
                configured=configured in {"microsoft_agent_framework", "maf"},
            ),
            self._provider(
                key="crewai",
                name="CrewAI",
                role="crew_workflow_sidecar",
                license_note="verify before vendoring; prefer sidecar",
                integration_mode="sidecar_http",
                strengths=["role_based_crews", "workflow_automation", "human_readable_tasks"],
                recommended=False,
                configured=configured == "crewai",
            ),
            self._provider(
                key="autogen",
                name="AutoGen",
                role="maintenance_multi_agent_reference",
                license_note="maintenance-mode; avoid new hard dependency",
                integration_mode="reference_or_migration_only",
                strengths=["agentchat_patterns", "multi_agent_research", "migration_lessons"],
                recommended=False,
                configured=configured == "autogen",
            ),
        ]

    def absorption_plan(self) -> dict[str, Any]:
        providers = self.providers()
        configured = [item for item in providers if item["configured"]]
        recommended = [item["key"] for item in providers if item["recommended"]]
        return {
            "mode": "aia_native_core_with_optional_sidecars",
            "configured_provider": settings.agent_framework_provider,
            "configured_enabled": settings.agent_framework_enabled,
            "configured_base_url": settings.agent_framework_base_url,
            "active_providers": configured,
            "recommended_stack": recommended,
            "do_not_vendor_by_default": True,
            "reason": "license_dependency_latency_isolation",
            "absorption_steps": [
                "keep_robot_ops_tick_as_authoritative_contract",
                "connect_openai_compatible_llm_for_reasoning_only",
                "run_langgraph_or_maf_as_sidecar_for_long_horizon_ops",
                "feed_sidecar_recommendations_back_as_runtime_bias_not_raw_actions",
                "server_still_validates_every_action",
            ],
            "safety_rules": [
                "external_agents_never_execute_game_actions_directly",
                "external_agents_can_only_write_recommendations_or_runtime_bias",
                "AIA_policy_engine_remains_final_decision_layer",
                "game_server_remains_final_execution_validator",
            ],
        }

    def _provider(
        self,
        key: str,
        name: str,
        role: str,
        license_note: str,
        integration_mode: str,
        strengths: list[str],
        recommended: bool,
        configured: bool,
    ) -> dict[str, Any]:
        return {
            "key": key,
            "name": name,
            "role": role,
            "license_note": license_note,
            "integration_mode": integration_mode,
            "strengths": strengths,
            "recommended": recommended,
            "configured": bool(configured),
        }


open_agent_provider_service = OpenAgentProviderService()
