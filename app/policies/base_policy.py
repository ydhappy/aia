from app.models.request_models import AgentState
from app.models.response_models import DecideResponse


class BaseRolePolicy:
    role_name = "base"

    def applies(self, role: str) -> bool:
        return role == self.role_name

    def decide(self, state: AgentState, profile: dict, recent_events: list[dict]) -> DecideResponse | None:
        raise NotImplementedError
