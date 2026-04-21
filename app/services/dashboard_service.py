from app.models.dashboard_models import AgentFilterResult, DashboardCountsResponse, ShardAssignmentResponse
from app.services.automation_service import automation_service
from app.services.recovery_service import recovery_service
from app.services.store_factory import store


class DashboardService:
    def counts(self, agent_ids: list[str]) -> DashboardCountsResponse:
        total_agents = len(agent_ids)
        active_agents = 0
        agents_with_tasks = 0
        agents_with_learning = 0
        agents_with_trace = 0
        agents_needing_recovery = 0

        for agent_id in agent_ids:
            if store.get_state(agent_id):
                active_agents += 1
            if automation_service.list_tasks(agent_id).tasks:
                agents_with_tasks += 1
            if store.get_learning_state(agent_id):
                agents_with_learning += 1
            if store.get_trace(agent_id):
                agents_with_trace += 1
            if recovery_service.recover_agent(agent_id).action not in {"stable", "noop"}:
                agents_needing_recovery += 1

        return DashboardCountsResponse(
            total_agents=total_agents,
            active_agents=active_agents,
            agents_with_tasks=agents_with_tasks,
            agents_with_learning=agents_with_learning,
            agents_with_trace=agents_with_trace,
            agents_needing_recovery=agents_needing_recovery,
        )

    def filter_agents(self, agent_ids: list[str], require_tasks: bool = False, require_learning: bool = False) -> AgentFilterResult:
        result = []
        for agent_id in agent_ids:
            if require_tasks and not automation_service.list_tasks(agent_id).tasks:
                continue
            if require_learning and not store.get_learning_state(agent_id):
                continue
            result.append(agent_id)
        return AgentFilterResult(agent_ids=result)

    def shard_assign(self, agent_ids: list[str], shard_count: int) -> list[ShardAssignmentResponse]:
        shard_count = max(shard_count, 1)
        buckets = [[] for _ in range(shard_count)]
        for idx, agent_id in enumerate(agent_ids):
            buckets[idx % shard_count].append(agent_id)
        return [ShardAssignmentResponse(shard_key=f"shard_{i}", agent_ids=bucket) for i, bucket in enumerate(buckets)]


dashboard_service = DashboardService()
