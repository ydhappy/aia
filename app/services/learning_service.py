from app.core.config import settings
from app.models.request_models import RobotFeedbackRequest
from app.models.response_models import RobotFeedbackResponse, RobotLearningStateResponse
from app.services.group_learning_service import group_learning_service
from app.services.growth_service import growth_service
from app.services.store_factory import store


class LearningService:
    def submit_feedback(self, request: RobotFeedbackRequest) -> RobotFeedbackResponse:
        current = store.get_learning_state(request.agent_id) or {}
        action_stats = current.get("action_stats", {})
        map_stats = current.get("map_action_stats", {})
        map_id = str(request.context.get("map_id", "global"))

        self._apply_decay(action_stats)
        self._apply_decay(map_stats.get(map_id, {}))

        global_stat = action_stats.get(
            request.action,
            {"count": 0, "reward_sum": 0.0, "success": 0, "failure": 0},
        )
        map_bucket = map_stats.get(map_id, {})
        map_stat = map_bucket.get(
            request.action,
            {"count": 0, "reward_sum": 0.0, "success": 0, "failure": 0},
        )

        for stat in (global_stat, map_stat):
            stat["count"] += 1
            stat["reward_sum"] += request.reward
            if request.outcome == "success":
                stat["success"] += 1
            elif request.outcome == "failure":
                stat["failure"] += 1

        action_stats[request.action] = global_stat
        map_bucket[request.action] = map_stat
        map_stats[map_id] = map_bucket

        current["action_stats"] = action_stats
        current["map_action_stats"] = map_stats
        current["last_feedback"] = request.model_dump()
        current["preferred_action"] = self._preferred_action(action_stats)
        current["avoid_action"] = self._avoid_action(action_stats)
        current["preferred_action_by_map"] = {
            key: self._preferred_action(value) for key, value in map_stats.items()
        }
        current["avoid_action_by_map"] = {
            key: self._avoid_action(value) for key, value in map_stats.items()
        }

        store.save_learning_state(request.agent_id, current)
        growth_service.update_from_feedback(request.agent_id, request.model_dump())

        group_key = request.context.get("group_key") or request.context.get("party_id") or request.context.get("role")
        if group_key:
            group_learning_service.update_group_learning(str(group_key), request.action, request.reward)

        return RobotFeedbackResponse(agent_id=request.agent_id)

    def get_learning_state(self, agent_id: str) -> RobotLearningStateResponse:
        return RobotLearningStateResponse(
            agent_id=agent_id,
            learning_state=store.get_learning_state(agent_id),
        )

    def _apply_decay(self, action_stats: dict) -> None:
        for stat in action_stats.values():
            stat["reward_sum"] = float(stat.get("reward_sum", 0.0)) * settings.learning_reward_decay

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
