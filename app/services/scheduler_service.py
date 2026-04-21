from app.core.config import settings
from app.services.watchdog_service import watchdog_service


class SchedulerService:
    def run_cycle(self, agent_ids: list[str]) -> dict:
        batch_size = max(1, settings.scheduler_cycle_batch_size)
        batches = [agent_ids[i:i + batch_size] for i in range(0, len(agent_ids), batch_size)]
        recovery_results = []
        for batch in batches:
            recovery_results.extend(watchdog_service.scan_and_recover(batch))
        return {
            "cycle_size": len(agent_ids),
            "batch_size": batch_size,
            "batch_count": len(batches),
            "recovery_results": recovery_results,
        }


scheduler_service = SchedulerService()
