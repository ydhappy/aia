from app.services.watchdog_service import watchdog_service


class SchedulerService:
    def run_cycle(self, agent_ids: list[str]) -> dict:
        recovery_results = watchdog_service.scan_and_recover(agent_ids)
        return {
            "cycle_size": len(agent_ids),
            "recovery_results": recovery_results,
        }


scheduler_service = SchedulerService()
