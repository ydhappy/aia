from app.models.request_models import DecideRequest, ObserveRequest
from app.models.response_models import DecideResponse, ObserveResponse
from app.services.llm_client import llm_client
from app.services.policy_engine import policy_engine
from app.services.state_store import state_store
from app.utils.validators import action_validator


class AgentService:
    def observe(self, request: ObserveRequest) -> ObserveResponse:
        state_store.save_state(
            agent_id=request.agent_id,
            tick=request.tick,
            state=request.state.model_dump(),
        )
        return ObserveResponse(agent_id=request.agent_id, tick=request.tick)

    def decide(self, request: DecideRequest) -> DecideResponse:
        state_store.increment_decide()
        profile = state_store.get_profile(request.agent_id)
        recent_events = state_store.get_recent_events(request.agent_id)

        if llm_client.should_use_llm(request.state.model_dump()):
            llm_result = llm_client.decide(
                {
                    "agent_id": request.agent_id,
                    "state": request.state.model_dump(),
                    "profile": profile,
                    "recent_events": recent_events,
                }
            )
            if llm_result:
                decision = DecideResponse(
                    action="IDLE",
                    action_args={},
                    confidence=0.50,
                    reason="llm_response_received_but_rule_safe_mode_enabled",
                    source="llm",
                )
                valid, reason = action_validator.validate(decision, request.state)
                if valid:
                    return decision

        try:
            decision = policy_engine.decide(
                request.state,
                profile=profile,
                recent_events=recent_events,
            )
            valid, reason = action_validator.validate(decision, request.state)
            if valid:
                return decision

            state_store.increment_fallback()
            return DecideResponse(
                action="IDLE",
                action_args={},
                confidence=0.20,
                reason=f"fallback_due_to_invalid_decision:{reason}",
                source="fallback",
            )
        except Exception:
            state_store.increment_fallback()
            return DecideResponse(
                action="IDLE",
                action_args={},
                confidence=0.10,
                reason="fallback_due_to_internal_error",
                source="fallback",
            )


agent_service = AgentService()
