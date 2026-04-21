from app.services.store_factory import store


class MemorySummaryService:
    def summarize_agent(self, agent_id: str) -> dict:
        profile = store.get_profile(agent_id) or {}
        learning = store.get_learning_state(agent_id) or {}
        trace = store.get_trace(agent_id) or {}
        return {
            "agent_id": agent_id,
            "role": profile.get("role"),
            "style": profile.get("style"),
            "preferred_action": learning.get("preferred_action"),
            "avoid_action": learning.get("avoid_action"),
            "last_reason": trace.get("final_reason"),
        }


memory_summary_service = MemorySummaryService()
