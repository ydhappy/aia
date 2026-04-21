from app.graphs.agent_graph import agent_graph
from app.models.request_models import DecideRequest, ObserveRequest
from app.models.response_models import AgentTraceResponse, DecideResponse, ObserveResponse
from app.services.llm_client import llm_client
from app.services.llm_parser import llm_parser
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

    def get_trace(self, agent_id: str) -> AgentTraceResponse:
        return AgentTraceResponse(agent_id=agent_id, trace=state_store.get_trace(agent_id))

    def decide(self, request: DecideRequest) -> DecideResponse:
        state_store.increment_decide()
        profile = state_store.get_profile(request.agent_id)
        recent_events = state_store.get_recent_events(request.agent_id)

        trace = agent_graph.run(
            agent_id=request.agent_id,
            state=request.state,
            profile=profile,
            recent_events=recent_events,
        )
        state_store.save_trace(request.agent_id, trace)

        if trace.get("llm_hint"):
            llm_result = llm_client.decide(trace)
            if llm_result:
                parsed = llm_parser.parse_decision(llm_result.get("raw", ""))
                if parsed:
                    valid, reason = action_validator.validate(parsed, request.state)
                    if valid:
                        return parsed
                    trace["llm_validation_error"] = reason
                    state_store.save_trace(request.agent_id, trace)

        try:
            decision = policy_engine.decide(
                request.state,
                profile=profile,
                recent_events=recent_events,
            )
            valid, reason = action_validator.validate(decision, request.state)
            if valid:
                trace["final_source"] = decision.source
                trace["final_reason"] = decision.reason
                state_store.save_trace(request.agent_id, trace)
                return decision

            state_store.increment_fallback()
            fallback = DecideResponse(
                action="IDLE",
                action_args={},
                confidence=0.20,
                reason=f"fallback_due_to_invalid_decision:{reason}",
                source="fallback",
            )
            trace["final_source"] = fallback.source
            trace["final_reason"] = fallback.reason
            state_store.save_trace(request.agent_id, trace)
            return fallback
        except Exception:
            state_store.increment_fallback()
            fallback = DecideResponse(
                action="IDLE",
                action_args={},
                confidence=0.10,
                reason="fallback_due_to_internal_error",
                source="fallback",
            )
            trace["final_source"] = fallback.source
            trace["final_reason"] = fallback.reason
            state_store.save_trace(request.agent_id, trace)
            return fallback


agent_service = AgentService()
