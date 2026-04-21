from app.services.growth_service import growth_service
from app.services.store_factory import store


class AutonomousGrowthService:
    def rebalance_runtime(self, agent_id: str) -> dict:
        growth = growth_service.get_growth_state(agent_id).model_dump()
        current = store.get_learning_state(f"autogrowth::{agent_id}") or {}
        stage = growth.get("stage", "novice")
        mastery = growth.get("mastery", {}) or {}
        failure_tags = growth.get("failure_tags", []) or []

        runtime_bias = current.get("runtime_bias", {})
        if stage == "novice":
            runtime_bias["risk_mode"] = "safe"
            runtime_bias["llm_mode"] = "restricted"
            runtime_bias["retreat_bonus"] = 5
        elif stage == "stable":
            runtime_bias["risk_mode"] = "balanced"
            runtime_bias["llm_mode"] = "selective"
            runtime_bias["retreat_bonus"] = 2
        elif stage == "optimized":
            runtime_bias["risk_mode"] = "efficient"
            runtime_bias["llm_mode"] = "selective"
            runtime_bias["retreat_bonus"] = 0
        else:
            runtime_bias["risk_mode"] = "advanced"
            runtime_bias["llm_mode"] = "selective"
            runtime_bias["retreat_bonus"] = -2

        if "retreat_timing_bad" in failure_tags[-5:]:
            runtime_bias["retreat_bonus"] = max(int(runtime_bias.get("retreat_bonus", 0)), 5)
            runtime_bias["risk_mode"] = "safe"
        if "inventory_management_bad" in failure_tags[-5:]:
            runtime_bias["inventory_mode"] = "strict"
        if mastery.get("support", 0.0) > mastery.get("fighter", 0.0):
            runtime_bias["preferred_role_bias"] = "support"

        current["stage"] = stage
        current["runtime_bias"] = runtime_bias
        store.save_learning_state(f"autogrowth::{agent_id}", current)
        return current


autonomous_growth_service = AutonomousGrowthService()
