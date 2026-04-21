from app.models.orchestration_models import FleetSummaryResponse, FleetSyncResponse
from app.services.automation_service import automation_service
from app.services.store_factory import store


class FleetService:
    def build_batches(self, agent_ids: list[str], batch_size: int, shard_key: str | None = None) -> FleetSyncResponse:
        batches = [agent_ids[i:i + batch_size] for i in range(0, len(agent_ids), batch_size)]
        return FleetSyncResponse(total_agents=len(agent_ids), shard_key=shard_key, batches=batches)

    def fleet_summary(self, agent_ids: list[str]) -> FleetSummaryResponse:
        total_agents = len(agent_ids)
        active_agents = sum(1 for agent_id in agent_ids if store.get_state(agent_id))
        robots_with_tasks = sum(1 for agent_id in agent_ids if automation_service.list_tasks(agent_id).tasks)
        robots_with_learning = sum(1 for agent_id in agent_ids if store.get_learning_state(agent_id))
        robots_with_trace = sum(1 for agent_id in agent_ids if store.get_trace(agent_id))
        return FleetSummaryResponse(
            total_agents=total_agents,
            active_agents=active_agents,
            robots_with_tasks=robots_with_tasks,
            robots_with_learning=robots_with_learning,
            robots_with_trace=robots_with_trace,
        )


fleet_service = FleetService()
