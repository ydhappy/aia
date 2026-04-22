from app.core.config import settings
from app.models.request_models import AgentState
from app.models.response_models import DecideResponse
from app.policies import ROLE_POLICIES
from app.services.adaptive_policy import adaptive_policy
from app.services.robot_ai_ops_service import robot_ai_ops_service


class PolicyEngine:
    def decide(
        self,
        state: AgentState,
        profile: dict | None = None,
        recent_events: list[dict] | None = None,
        learning_state: dict | None = None,
        runtime_override: dict | None = None,
        growth_state: dict | None = None,
    ) -> DecideResponse:
        profile = profile or {}
        recent_events = recent_events or []
        learning_state = learning_state or {}
        runtime_override = runtime_override or {}
        growth_state = growth_state or {}

        override = runtime_override.get("override", {}) if isinstance(runtime_override, dict) else {}
        runtime_bias = runtime_override.get("runtime_bias", {}) if isinstance(runtime_override, dict) else {}
        if not isinstance(runtime_bias, dict):
            runtime_bias = {}
        effective_learning = self._learning_for_map(learning_state, state.map_id)
        potion_count = state.inventory.get("potion", 0)
        role = override.get("role", profile.get("role", "custom"))
        style = override.get("style", profile.get("style", "balanced"))
        patrol_points = override.get("patrol_points", profile.get("patrol_points", []))
        retreat_hp_threshold = int(override.get("retreat_hp_threshold", settings.default_retreat_hp_threshold))
        forced_action = override.get("forced_action")
        forced_mode = self._safe_move_mode(override.get("forced_mode") or runtime_bias.get("move_mode"), state)
        growth_stage = growth_state.get("stage", "novice")
        retreat_hp_threshold = min(95, max(1, retreat_hp_threshold + int(runtime_bias.get("retreat_bonus", 0) or 0)))
        risk_mode = str(runtime_bias.get("risk_mode", "") or "")
        if risk_mode == "safe" and style == "balanced":
            style = "defensive"
        elif risk_mode in {"efficient", "advanced"} and style == "balanced":
            style = "aggressive"

        if growth_stage == "novice":
            retreat_hp_threshold = max(retreat_hp_threshold, settings.default_retreat_hp_threshold + 5)
            if style == "balanced":
                style = "defensive"
        elif growth_stage in {"optimized", "expert"} and style == "balanced":
            style = "aggressive"

        has_danger_event = any(event.get("severity") == "high" for event in recent_events)
        is_overweight = state.weight_percent is not None and state.weight_percent >= 85
        infinite_healing = state.inventory.get("infinite_healing_potion", 0)
        risk_assessment = robot_ai_ops_service.assess_state(state)
        navigation_plan = robot_ai_ops_service.choose_navigation(
            state,
            profile,
            effective_learning,
            runtime_bias,
            agent_id=str(profile.get("agent_id") or ""),
        )

        if forced_action in {"MOVE", "ATTACK", "USE_SKILL", "RETREAT", "PICKUP", "IDLE"}:
            return adaptive_policy.adjust(DecideResponse(
                action=forced_action,
                action_args=self._with_navigation({"mode": forced_mode} if forced_mode else {}, navigation_plan),
                confidence=0.99,
                reason="runtime_override_forced_action",
                source="rule_engine",
            ), effective_learning)

        if risk_assessment.get("should_retreat") and state.hp <= 35 and not state.safe_zone:
            item_hint = "infinite_healing_potion" if infinite_healing > 0 else "potion" if potion_count > 0 else ""
            return adaptive_policy.adjust(DecideResponse(
                action="RETREAT",
                action_args=self._with_navigation({
                    "mode": navigation_plan.get("mode") or ("teleport" if state.can_teleport else "safe_zone"),
                    "role": role,
                    "growth_stage": growth_stage,
                    "risk_score": risk_assessment.get("risk_score", 0),
                    "use_hp_item_first": bool(item_hint),
                    "item": item_hint,
                }, navigation_plan),
                confidence=0.99,
                reason="critical_hp_retreat_before_heal:" + ",".join(risk_assessment.get("reasons", [])[:3]),
                source="rule_engine",
            ), effective_learning)

        if state.must_use_hp_item and infinite_healing > 0:
            return adaptive_policy.adjust(DecideResponse(
                action="USE_SKILL",
                action_args=self._with_navigation({"skill": "heal", "item": "infinite_healing_potion", "target": "self", "growth_stage": growth_stage}, navigation_plan),
                confidence=0.98,
                reason="hp_below_95_use_infinite_healing",
                source="rule_engine",
            ), effective_learning)

        if state.must_use_hp_item and potion_count > 0:
            return adaptive_policy.adjust(DecideResponse(
                action="USE_SKILL",
                action_args=self._with_navigation({"skill": "heal", "item": "potion", "target": "self", "growth_stage": growth_stage}, navigation_plan),
                confidence=0.93,
                reason="hp_below_95_use_available_potion",
                source="rule_engine",
            ), effective_learning)

        if state.must_use_hp_item and runtime_bias.get("inventory_mode") == "strict" and not state.safe_zone:
            return adaptive_policy.adjust(DecideResponse(
                action="RETREAT",
                action_args=self._with_navigation({"mode": "restock_or_recover", "role": role, "growth_stage": growth_stage}, navigation_plan),
                confidence=0.90,
                reason="strict_inventory_without_infinite_healing",
                source="rule_engine",
            ), effective_learning)

        if risk_assessment.get("should_retreat"):
            return adaptive_policy.adjust(DecideResponse(
                action="RETREAT",
                action_args=self._with_navigation({
                    "mode": navigation_plan.get("mode") or ("teleport" if state.can_teleport else "safe_zone"),
                    "role": role,
                    "growth_stage": growth_stage,
                    "risk_score": risk_assessment.get("risk_score", 0),
                }, navigation_plan),
                confidence=0.97,
                reason="aia_ops_high_risk:" + ",".join(risk_assessment.get("reasons", [])[:3]),
                source="rule_engine",
            ), effective_learning)

        if (state.hp <= retreat_hp_threshold or has_danger_event) and not state.safe_zone:
            mode = override.get("retreat_mode") or ("teleport" if state.can_teleport else "safe_zone")
            return adaptive_policy.adjust(DecideResponse(
                action="RETREAT",
                action_args=self._with_navigation({"mode": mode, "role": role, "growth_stage": growth_stage}, navigation_plan),
                confidence=0.99,
                reason="critical_hp_or_high_severity_event",
                source="rule_engine",
            ), effective_learning)

        if is_overweight and not state.safe_zone:
            return adaptive_policy.adjust(DecideResponse(
                action="RETREAT",
                action_args=self._with_navigation({"mode": "inventory_reset", "growth_stage": growth_stage}, navigation_plan),
                confidence=0.87,
                reason="inventory_weight_high",
                source="rule_engine",
            ), effective_learning)

        for policy in ROLE_POLICIES:
            if policy.applies(role):
                decision = policy.decide(state, profile, recent_events)
                if decision is not None:
                    decision.action_args = {**decision.action_args, "growth_stage": growth_stage}
                    if runtime_bias.get("move_mode") and decision.action == "MOVE":
                        decision.action_args = self._with_navigation({**decision.action_args, "mode": self._safe_move_mode(runtime_bias.get("move_mode"), state)}, navigation_plan)
                        decision.reason = f"{decision.reason}|runtime_move_bias"
                    elif decision.action == "MOVE":
                        decision.action_args = self._with_navigation({
                            **decision.action_args,
                            "mode": self._safe_move_mode(decision.action_args.get("mode"), state),
                        }, navigation_plan)
                    else:
                        decision.action_args = self._with_navigation(decision.action_args, navigation_plan)
                    return adaptive_policy.adjust(decision, effective_learning)

        if state.hp <= settings.default_heal_hp_threshold and state.cooldowns.get("heal", 999) == 0:
            return adaptive_policy.adjust(DecideResponse(
                action="USE_SKILL",
                action_args=self._with_navigation({"skill": "heal", "target": "self", "growth_stage": growth_stage}, navigation_plan),
                confidence=0.92,
                reason="low_hp_and_heal_ready",
                source="rule_engine",
            ), effective_learning)

        if state.hp <= settings.default_heal_hp_threshold and potion_count > 0:
            return adaptive_policy.adjust(DecideResponse(
                action="PICKUP",
                action_args=self._with_navigation({"item": "potion_buffer", "growth_stage": growth_stage}, navigation_plan),
                confidence=0.60,
                reason="low_hp_and_need_resources",
                source="rule_engine",
            ), effective_learning)

        if style == "defensive" and state.is_under_attack and state.target_distance is not None and state.target_distance > 1 and not state.safe_zone:
            return adaptive_policy.adjust(DecideResponse(
                action="MOVE",
                action_args=self._with_navigation({"mode": self._safe_move_mode(runtime_bias.get("move_mode") or override.get("move_mode", "kite"), state), "target_id": state.target_id, "growth_stage": growth_stage}, navigation_plan),
                confidence=0.84,
                reason="defensive_style_kiting",
                source="rule_engine",
            ), effective_learning)

        if state.target_id and state.target_distance is not None and state.target_distance <= 1:
            return adaptive_policy.adjust(DecideResponse(
                action="ATTACK",
                action_args=self._with_navigation({"target_id": state.target_id, "style": style, "growth_stage": growth_stage}, navigation_plan),
                confidence=0.95 if growth_stage != "novice" else 0.88,
                reason="target_in_melee_range",
                source="rule_engine",
            ), effective_learning)

        if state.target_id and state.target_distance is not None and state.target_distance > 1:
            return adaptive_policy.adjust(DecideResponse(
                action="MOVE",
                action_args=self._with_navigation({"target_id": state.target_id, "mode": self._safe_move_mode(runtime_bias.get("move_mode") or override.get("move_mode", "approach"), state), "growth_stage": growth_stage}, navigation_plan),
                confidence=0.85,
                reason="target_visible_but_not_in_range",
                source="rule_engine",
            ), effective_learning)

        if patrol_points:
            return adaptive_policy.adjust(DecideResponse(
                action="MOVE",
                action_args=self._with_navigation({"mode": self._safe_move_mode(runtime_bias.get("move_mode") or override.get("move_mode", "patrol"), state), "points": patrol_points[:3], "growth_stage": growth_stage}, navigation_plan),
                confidence=0.70,
                reason="patrol_route_available",
                source="rule_engine",
            ), effective_learning)

        if navigation_plan.get("algorithm") in {
            "frontier_roam",
            "spawn_anchor",
            "dungeon_sweep",
            "party_rally",
            "siege_attack",
            "siege_defense",
            "teleport_hunt",
            "pc_auto_hunt_sync",
        } and not state.safe_zone:
            return adaptive_policy.adjust(DecideResponse(
                action="MOVE",
                action_args=self._with_navigation({
                    "mode": self._safe_move_mode(navigation_plan.get("mode"), state),
                    "growth_stage": growth_stage,
                }, navigation_plan),
                confidence=0.72,
                reason="aia_navigation_plan:" + str(navigation_plan.get("reason", "")),
                source="rule_engine",
            ), effective_learning)

        return adaptive_policy.adjust(DecideResponse(
            action="IDLE",
            action_args=self._with_navigation({"role": role, "growth_stage": growth_stage}, navigation_plan),
            confidence=0.80,
            reason="no_target_and_no_urgent_state",
            source="rule_engine",
        ), effective_learning)

    def _learning_for_map(self, learning_state: dict, map_id: int | None) -> dict:
        if not learning_state:
            return {}
        merged = dict(learning_state)
        map_key = str(map_id if map_id is not None else "global")
        preferred_by_map = learning_state.get("preferred_action_by_map") or {}
        avoid_by_map = learning_state.get("avoid_action_by_map") or {}
        if isinstance(preferred_by_map, dict) and preferred_by_map.get(map_key):
            merged["preferred_action"] = preferred_by_map.get(map_key)
        if isinstance(avoid_by_map, dict) and avoid_by_map.get(map_key):
            merged["avoid_action"] = avoid_by_map.get(map_key)
        return merged

    def _safe_move_mode(self, mode: object, state: AgentState) -> str:
        if mode is None:
            return ""
        value = str(mode)
        if state.safe_zone and value == "kite":
            return "patrol"
        return value

    def _with_navigation(self, action_args: dict, navigation_plan: dict) -> dict:
        merged = dict(action_args or {})
        if navigation_plan:
            merged.setdefault("nav_algorithm", navigation_plan.get("algorithm"))
            merged.setdefault("nav_reason", navigation_plan.get("reason"))
            merged.setdefault("risk_score", navigation_plan.get("risk_score"))
            merged.setdefault("risk_severity", navigation_plan.get("severity"))
            for key in (
                "points",
                "target_x",
                "target_y",
                "target_map_id",
                "spread_radius",
                "step_budget",
                "route_id",
                "hunt_zone",
                "autonomy_source",
                "operator_profile",
                "server_validation",
                "client_server_sync",
            ):
                value = navigation_plan.get(key)
                if value is not None:
                    merged.setdefault(key, value)
        return merged


policy_engine = PolicyEngine()
