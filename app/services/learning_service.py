from app.models.request_models import RobotFeedbackRequest
from app.models.response_models import RobotFeedbackResponse, RobotLearningStateResponse
from app.services.store_factory import store


class LearningService:
    def submit_feedback(self, request: RobotFeedbackRequest) -> RobotFeedbackResponse:
        current = store.get_learning_state(request.agent_id) or {}
        action_stats = current.get("action_stats", {})
        stat = action_stats.get(
            request.action,
            {"count": 0, "reward_sum": 0.0, "success": 0, "failure": 0},
        )

        stat["count"] += 1
        stat["reward_sum"] += request.reward
        if request.outcome == "success":
            stat["success"] += 1
        elif request.outcome == "failure":
            stat["failure"] += 1

        action_stats[request.action] = stat
        current["action_stats"] = action_stats
        current["last_feedback"] = request.model_dump()
        current["preferred_action"] = self._preferred_action(action_stats)
        current["avoid_action"] = self._avoid_action(action_stats)

        store.save_learning_state(request.agent_id, current)
        return RobotFeedbackResponse(agent_id=request.agent_id)

    def get_learning_state(self, agent_id: str) -> RobotLearningStateResponse:
        return RobotLearningStateResponse(
            agent_id=agent_id,
            learning_state=store.get_learning_state(agent_id),
        )

    def _preferred_action(self, action_stats: dict) -> str | None:
        best_action = None
        best_score = None
        for action, stat in action_stats.items():
            count = max(stat.get("count", 0), 1)
            score = stat.get("reward_sum", 0.0) / count
            if best_score is None or score > best_score:
                best_score = score
                best_action = action
        return best_action

    def _avoid_action(self, action_stats: dict) -> str | None:
        worst_action = None
        worst_score = None
        for action, stat in action_stats.items():
            count = max(stat.get("count", 0), 1)
            score = stat.get("reward_sum", 0.0) / count
            if worst_score is None or score < worst_score:
                worst_score = score
                worst_action = action
        return worst_action


learning_service = LearningService()
