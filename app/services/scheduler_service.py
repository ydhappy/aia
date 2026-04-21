from app.core.config import settings
from app.services.autonomous_growth_service import autonomous_growth_service
from app.services.watchdog_service import watchdog_service


class SchedulerService:
    def run_cycle(self, agent_ids: list[str]) -> dict:
        batch_size = max(1, settings.scheduler_cycle_batch_size)
        batches = [agent_ids[i:i + batch_size] for i in range(0, len(agent_ids), batch_size)]
        recovery_results = []
        growth_updates = []
        for batch in batches:
            recovery_results.extend(watchdog_service.scan_and_recover(batch))
            for agent_id in batch:
                growth_updates.append({"agent_id": agent_id, "runtime": autonomous_growth_service.rebalance_runtime(agent_id)})
        return {
            "cycle_size": len(agent_ids),
            "batch_size": batch_size,
            "batch_count": len(batches),
            "recovery_results": recovery_results,
            "growth_updates": growth_updates,
        }


scheduler_service = SchedulerService()
