from app.models.request_models import AgentState


def build_profile_hint(state: AgentState, profile: dict) -> dict:
    return {
        "role": profile.get("role", "custom"),
        "style": profile.get("style", "balanced"),
        "nearby_allies": state.nearby_allies,
        "nearby_enemies": state.nearby_enemies,
        "weight_percent": state.weight_percent,
        "preferred_skills": profile.get("preferred_skills", []),
        "patrol_points": profile.get("patrol_points", []),
    }
