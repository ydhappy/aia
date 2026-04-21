from app.core.config import settings
from app.graphs.agent_graph import agent_graph
from app.models.batch_models import BatchDecideResponse, BatchObserveResponse
from app.models.request_models import DecideRequest, ObserveRequest
from app.models.response_models import AgentTraceResponse, DecideResponse, ObserveResponse
from app.services.group_learning_service import group_learning_service
from app.services.growth_service import growth_service
from app.services.llm_client import llm_client
from app.services.llm_parser import llm_parser
from app.services.policy_engine import policy_engine
from app.services.runtime_overrides import runtime_overrides
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

    def _compact_trace(self, trace: dict) -> dict:
        if not settings.trace_store_enabled:
            return {}
        if not settings.trace_compact_mode:
            return trace
        compact = {
            "agent_id": trace.get("agent_id"),
            "risk_score": trace.get("risk_score"),
            "strategy": trace.get("strategy"),
            "llm_hint": trace.get("llm_hint"),
            "profile_hint": trace.get("profile_hint"),
            "runtime_override": trace.get("runtime_override"),
            "growth_state": trace.get("growth_state"),
            "final_source": trace.get("final_source"),
            "final_reason": trace.get("final_reason"),
            "learning_state": trace.get("learning_state"),
        }
        return compact

    def decide(self, request: DecideRequest) -> DecideResponse:
        store.increment_decide()
        profile = store.get_profile(request.agent_id)
        recent_events = store.get_recent_events(request.agent_id)
        learning_state = store.get_learning_state(request.agent_id)
        growth_state = growth_service.get_growth_state(request.agent_id).model_dump()

        group_key = profile.get("party_id") or profile.get("role")
        if group_key:
            merged_learning = group_learning_service.merge_group_learning(request.agent_id, group_key)
            learning_state = {**learning_state, **{k: v for k, v in merged_learning.items() if k in ["preferred_action", "avoid_action"]}}

        override_info = runtime_overrides.get_override(profile, request.state.model_dump())

        trace = agent_graph.run(
            agent_id=request.agent_id,
            state=request.state,
            profile=profile,
            recent_events=recent_events,
            learning_state=learning_state,
        )
        trace["runtime_override"] = override_info
        trace["growth_state"] = growth_state
        store.save_trace(request.agent_id, self._compact_trace(trace))

        if trace.get("llm_hint"):
            llm_result = llm_client.decide(trace)
            if llm_result:
                parsed = llm_parser.parse_decision(llm_result.get("raw", ""))
                if parsed:
                    valid, reason = action_validator.validate(parsed, request.state)
                    if valid:
                        trace["final_source"] = parsed.source
                        trace["final_reason"] = parsed.reason
                        store.save_trace(request.agent_id, self._compact_trace(trace))
                        return parsed
                    trace["llm_validation_error"] = reason
                    store.save_trace(request.agent_id, self._compact_trace(trace))

        try:
            decision = policy_engine.decide(
                request.state,
                profile=profile,
                recent_events=recent_events,
                learning_state=learning_state,
                runtime_override=override_info,
                growth_state=growth_state,
            )
            valid, reason = action_validator.validate(decision, request.state)
            if valid:
                trace["final_source"] = decision.source
                trace["final_reason"] = decision.reason
                trace["learning_preferred_action"] = learning_state.get("preferred_action")
                trace["learning_avoid_action"] = learning_state.get("avoid_action")
                trace["growth_stage"] = growth_state.get("stage")
                store.save_trace(request.agent_id, self._compact_trace(trace))
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
            store.save_trace(request.agent_id, self._compact_trace(trace))
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
            store.save_trace(request.agent_id, self._compact_trace(trace))
            return fallback

    def decide_batch(self, requests: list[DecideRequest]) -> BatchDecideResponse:
        return BatchDecideResponse(items=[self.decide(request) for request in requests])


agent_service = AgentService()
