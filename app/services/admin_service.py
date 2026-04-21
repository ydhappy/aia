from app.models.admin_models import AdminRobotSummaryResponse, AdminSystemSummaryResponse
from app.services.automation_service import automation_service
from app.services.store_factory import store


class AdminService:
    def robot_summary(self, agent_id: str) -> AdminRobotSummaryResponse:
        has_state = bool(store.get_state(agent_id))
        has_profile = bool(store.get_profile(agent_id))
        has_trace = bool(store.get_trace(agent_id))
        has_learning = bool(store.get_learning_state(agent_id))
        active_tasks = len([t for t in automation_service.list_tasks(agent_id).tasks if t.status in {"pending", "running"}])
        return AdminRobotSummaryResponse(
            agent_id=agent_id,
            has_state=has_state,
            has_profile=has_profile,
            has_trace=has_trace,
            has_learning=has_learning,
            active_tasks=active_tasks,
        )

    def system_summary(self, agent_ids: list[str]) -> AdminSystemSummaryResponse:
        return AdminSystemSummaryResponse(
            robots=[self.robot_summary(agent_id) for agent_id in agent_ids]
        )


admin_service = AdminService()
