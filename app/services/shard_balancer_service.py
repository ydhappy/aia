from app.services.automation_service import automation_service
from app.services.store_factory import store


class ShardBalancerService:
    def weighted_assign(self, agent_ids: list[str], shard_count: int) -> list[dict]:
        shard_count = max(shard_count, 1)
        shards = [{"shard_key": f"shard_{i}", "agent_ids": [], "weight": 0} for i in range(shard_count)]
        weighted_agents = []
        for agent_id in agent_ids:
            weight = 1
            if store.get_state(agent_id):
                weight += 1
            if store.get_learning_state(agent_id):
                weight += 1
            if automation_service.list_tasks(agent_id).tasks:
                weight += 2
            weighted_agents.append((agent_id, weight))

        weighted_agents.sort(key=lambda item: item[1], reverse=True)
        for agent_id, weight in weighted_agents:
            target = min(shards, key=lambda item: item["weight"])
            target["agent_ids"].append(agent_id)
            target["weight"] += weight
        return shards


shard_balancer_service = ShardBalancerService()
