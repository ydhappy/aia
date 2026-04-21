from app.models.request_models import AgentState


def build_profile_hint(state: AgentState, profile: dict, learning_state: dict | None = None) -> dict:
    learning_state = learning_state or {}
    return {
        "role": profile.get("role", "custom"),
        "style": profile.get("style", "balanced"),
        "nearby_allies": state.nearby_allies,
        "nearby_enemies": state.nearby_enemies,
        "weight_percent": state.weight_percent,
        "preferred_skills": profile.get("preferred_skills", []),
        "patrol_points": profile.get("patrol_points", []),
        "preferred_action": learning_state.get("preferred_action"),
        "avoid_action": learning_state.get("avoid_action"),
    }
