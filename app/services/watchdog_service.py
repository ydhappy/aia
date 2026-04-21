from app.services.recovery_service import recovery_service


class WatchdogService:
    def scan_and_recover(self, agent_ids: list[str]) -> list[dict]:
        results = []
        for agent_id in agent_ids:
            result = recovery_service.recover_agent(agent_id)
            results.append(result.model_dump())
        return results


watchdog_service = WatchdogService()
