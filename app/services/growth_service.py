from app.models.growth_models import GrowthStateResponse
from app.services.failure_analysis_service import failure_analysis_service
from app.services.store_factory import store


class GrowthService:
    def update_from_feedback(self, agent_id: str, feedback: dict) -> GrowthStateResponse:
        current = store.get_learning_state(f"growth::{agent_id}") or {}
        scores = current.get("scores", {})
        mastery = current.get("mastery", {})
        failures = current.get("failure_tags", [])

        action = feedback.get("action", "UNKNOWN")
        reward = float(feedback.get("reward", 0.0) or 0.0)
        outcome = feedback.get("outcome", "partial")
        context = feedback.get("context", {}) or {}
        role = str(context.get("role", "general"))
        map_id = str(context.get("map_id", "global"))

        scores["overall"] = float(scores.get("overall", 0.0)) + reward
        scores[f"action::{action}"] = float(scores.get(f"action::{action}", 0.0)) + reward
        scores[f"role::{role}"] = float(scores.get(f"role::{role}", 0.0)) + reward
        scores[f"map::{map_id}"] = float(scores.get(f"map::{map_id}", 0.0)) + reward

        mastery[role] = float(mastery.get(role, 0.0)) + (1.0 if outcome == "success" else 0.25 if outcome == "partial" else -0.25)
        mastery[f"map::{map_id}"] = float(mastery.get(f"map::{map_id}", 0.0)) + (0.75 if outcome == "success" else -0.1)
        mastery[action] = float(mastery.get(action, 0.0)) + (0.5 if outcome == "success" else -0.25)

        failures.extend(failure_analysis_service.analyze(feedback))
        failures = failures[-30:]

        stage = self._stage(scores.get("overall", 0.0), failures)
        current["scores"] = scores
        current["mastery"] = mastery
        current["failure_tags"] = failures
        current["stage"] = stage
        store.save_learning_state(f"growth::{agent_id}", current)
        return GrowthStateResponse(agent_id=agent_id, stage=stage, scores=scores, mastery=mastery, failure_tags=failures)

    def get_growth_state(self, agent_id: str) -> GrowthStateResponse:
        current = store.get_learning_state(f"growth::{agent_id}") or {}
        return GrowthStateResponse(
            agent_id=agent_id,
            stage=current.get("stage", "novice"),
            scores=current.get("scores", {}),
            mastery=current.get("mastery", {}),
            failure_tags=current.get("failure_tags", []),
        )

    def _stage(self, overall: float, failures: list[str]) -> str:
        failure_penalty = len(failures[-10:])
        effective = overall - failure_penalty
        if effective >= 50:
            return "expert"
        if effective >= 20:
            return "optimized"
        if effective >= 5:
            return "stable"
        return "novice"


growth_service = GrowthService()
