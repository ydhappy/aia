from app.services.store_factory import store


class GroupLearningService:
    def merge_group_learning(self, agent_id: str, group_key: str) -> dict:
        agent_state = store.get_learning_state(agent_id) or {}
        group_state = store.get_learning_state(f"group::{group_key}") or {}

        merged = {
            "group_key": group_key,
            "agent_learning": agent_state,
            "group_learning": group_state,
            "preferred_action": agent_state.get("preferred_action") or group_state.get("preferred_action"),
            "avoid_action": agent_state.get("avoid_action") or group_state.get("avoid_action"),
        }
        return merged

    def update_group_learning(self, group_key: str, action: str, reward: float) -> dict:
        current = store.get_learning_state(f"group::{group_key}") or {}
        stats = current.get("action_stats", {})
        stat = stats.get(action, {"count": 0, "reward_sum": 0.0})
        stat["count"] += 1
        stat["reward_sum"] += reward
        stats[action] = stat
        current["action_stats"] = stats
        current["preferred_action"] = self._preferred_action(stats)
        current["avoid_action"] = self._avoid_action(stats)
        store.save_learning_state(f"group::{group_key}", current)
        return current

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


group_learning_service = GroupLearningService()
