from app.graphs.agent_graph import agent_graph
from app.models.batch_models import BatchDecideResponse, BatchObserveResponse
from app.models.request_models import DecideRequest, ObserveRequest
from app.models.response_models import AgentTraceResponse, DecideResponse, ObserveResponse
from app.services.llm_client import llm_client
from app.services.llm_parser import llm_parser
from app.services.policy_engine import policy_engine
from app.services.store_factory import store
from app.utils.validators import action_validator


class AgentService:
    def observe(self, request: ObserveRequest) -> ObserveResponse:
        store.save_state(
            agent_id=request.agent_id,
            tick=request.tick,
            state=request.state.model_dump(),
        )
        return ObserveResponse(agent_id=request.agent_id, tick=request.tick)

    def observe_batch(self, requests: list[ObserveRequest]) -> BatchObserveResponse:
        return BatchObserveResponse(items=[self.observe(request) for request in requests])

    def get_trace(self, agent_id: str) -> AgentTraceResponse:
        return AgentTraceResponse(agent_id=agent_id, trace=store.get_trace(agent_id))

    def decide(self, request: DecideRequest) -> DecideResponse:
        store.increment_decide()
        profile = store.get_profile(request.agent_id)
        recent_events = store.get_recent_events(request.agent_id)
        learning_state = store.get_learning_state(request.agent_id)

        trace = agent_graph.run(
            agent_id=request.agent_id,
            state=request.state,
            profile=profile,
            recent_events=recent_events,
            learning_state=learning_state,
        )
        store.save_trace(request.agent_id, trace)

        if trace.get("llm_hint"):
            llm_result = llm_client.decide(trace)
            if llm_result:
                parsed = llm_parser.parse_decision(llm_result.get("raw", ""))
                if parsed:
                    valid, reason = action_validator.validate(parsed, request.state)
                    if valid:
                        trace["final_source"] = parsed.source
                        trace["final_reason"] = parsed.reason
                        store.save_trace(request.agent_id, trace)
                        return parsed
                    trace["llm_validation_error"] = reason
                    store.save_trace(request.agent_id, trace)

        try:
            decision = policy_engine.decide(
                request.state,
                profile=profile,
                recent_events=recent_events,
                learning_state=learning_state,
            )
            valid, reason = action_validator.validate(decision, request.state)
            if valid:
                trace["final_source"] = decision.source
                trace["final_reason"] = decision.reason
                trace["learning_preferred_action"] = learning_state.get("preferred_action")
                trace["learning_avoid_action"] = learning_state.get("avoid_action")
                store.save_trace(request.agent_id, trace)
                return decision

            store.increment_fallback()
            fallback = DecideResponse(
                action="IDLE",
                action_args={},
                confidence=0.20,
                reason=f"fallback_due_to_invalid_decision:{reason}",
                source="fallback",
            )
            trace["final_source"] = fallback.source
            trace["final_reason"] = fallback.reason
            store.save_trace(request.agent_id, trace)
            return fallback
        except Exception:
            store.increment_fallback()
            fallback = DecideResponse(
                action="IDLE",
                action_args={},
                confidence=0.10,
                reason="fallback_due_to_internal_error",
                source="fallback",
            )
            trace["final_source"] = fallback.source
            trace["final_reason"] = fallback.reason
            store.save_trace(request.agent_id, trace)
            return fallback

    def decide_batch(self, requests: list[DecideRequest]) -> BatchDecideResponse:
        return BatchDecideResponse(items=[self.decide(request) for request in requests])


agent_service = AgentService()
