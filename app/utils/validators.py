from app.models.request_models import AgentState
from app.models.response_models import DecideResponse


ALLOWED_ACTIONS = {"MOVE", "ATTACK", "USE_SKILL", "RETREAT", "PICKUP", "IDLE"}


class ActionValidator:
    def validate(self, decision: DecideResponse, state: AgentState) -> tuple[bool, str]:
        if decision.action not in ALLOWED_ACTIONS:
            return False, "action_not_allowed"

        if decision.action == "ATTACK" and not state.target_id:
            return False, "attack_without_target"

        if decision.action == "MOVE" and state.safe_zone and decision.action_args.get("mode") == "kite":
            return False, "kite_not_needed_in_safe_zone"

        if decision.action == "USE_SKILL":
            skill = decision.action_args.get("skill")
            if not skill:
                return False, "skill_name_missing"
            if state.cooldowns.get(skill, 0) > 0:
                return False, "skill_on_cooldown"

        if decision.action == "RETREAT" and state.safe_zone:
            return False, "already_in_safe_zone"

        return True, "ok"


action_validator = ActionValidator()
