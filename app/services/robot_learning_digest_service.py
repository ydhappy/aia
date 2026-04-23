from collections import Counter, defaultdict
from typing import Any

from app.models.request_models import (
    RobotActionRecord,
    RobotFeedbackRequest,
    RobotLearningDigestRequest,
    RobotTalkMemoryRecord,
)
from app.models.response_models import RobotLearningDigestResponse
from app.services.autonomous_growth_service import autonomous_growth_service
from app.services.learning_service import learning_service
from app.services.robot_autonomy_baseline_service import robot_autonomy_baseline_service
from app.services.store_factory import store


class RobotLearningDigestService:
    def __init__(self) -> None:
        self._last_summary: dict[str, Any] = {
            "digests": 0,
            "processed_records": 0,
            "processed_talk_memories": 0,
            "issue_count": 0,
            "last_reason": "",
            "last_server": "",
            "recent_issues": [],
            "action_counts": {},
            "talk_topics": {},
        }

    def apply_digest(self, request: RobotLearningDigestRequest) -> RobotLearningDigestResponse:
        issues: list[dict[str, Any]] = []
        delete_uids: list[int] = []
        delete_talk_keys: list[dict[str, Any]] = []
        learning_updates = 0
        growth_updates = 0
        action_counts: Counter[str] = Counter()

        for record in request.records:
            action_counts[record.action_type] += 1
            feedback = self._feedback_from_record(record)
            if feedback is not None:
                learning_service.submit_feedback(feedback)
                autonomous_growth_service.rebalance_runtime(feedback.agent_id)
                learning_updates += 1
                growth_updates += 1
            record_issues = self._detect_issues(record)
            if record_issues:
                issues.extend(record_issues)
            delete_uids.append(record.uid)

        talk_updates = 0
        talk_topics: Counter[str] = Counter()
        for memory in request.talk_memories:
            if self._apply_talk_memory(memory):
                talk_updates += 1
                delete_talk_keys.append(self._talk_delete_key(memory))
            issues.extend(self._detect_talk_memory_issues(memory))
            topic = (memory.recent_topic or "일반").strip() or "일반"
            talk_topics[topic] += 1

        store.increment_learning_digest(len(request.records), len(issues))
        self._last_summary = {
            "digests": int(self._last_summary.get("digests", 0)) + 1,
            "processed_records": int(self._last_summary.get("processed_records", 0)) + len(request.records),
            "processed_talk_memories": int(self._last_summary.get("processed_talk_memories", 0)) + len(request.talk_memories),
            "issue_count": int(self._last_summary.get("issue_count", 0)) + len(issues),
            "last_reason": request.reason,
            "last_server": request.server_name,
            "recent_issues": (issues + list(self._last_summary.get("recent_issues", [])))[:20],
            "action_counts": self._merge_counts(self._last_summary.get("action_counts", {}), action_counts),
            "talk_topics": self._merge_counts(self._last_summary.get("talk_topics", {}), talk_topics),
        }

        return RobotLearningDigestResponse(
            processed_records=len(request.records),
            processed_talk_memories=len(request.talk_memories),
            delete_uids=delete_uids if request.delete_after_apply else [],
            delete_talk_keys=delete_talk_keys if request.delete_after_apply else [],
            issue_count=len(issues),
            issues=issues[:100],
            learning_updates=learning_updates,
            growth_updates=growth_updates,
            talk_updates=talk_updates,
            cleanup_policy=robot_autonomy_baseline_service.cleanup_policy(),
        )

    def summary(self) -> dict[str, Any]:
        metrics = store.metrics()
        return {
            **self._last_summary,
            "metrics": metrics,
            "learning_agents": self._estimate_learning_agents(),
        }

    def _feedback_from_record(self, record: RobotActionRecord) -> RobotFeedbackRequest | None:
        action, reward, outcome, role = self._classify_action(record)
        if action is None:
            return None
        action_type = record.action_type.lower()
        detail = (record.detail or "").lower()
        return RobotFeedbackRequest(
            agent_id=record.agent_id,
            tick=max(record.created_at, 0),
            action=action,
            reward=reward,
            outcome=outcome,
            context={
                "role": role,
                "map_id": record.loc_map,
                "loc_x": record.loc_x,
                "loc_y": record.loc_y,
                "source_uid": record.uid,
                "source_action": record.action_type,
                "detail": record.detail or "",
                "robot_uid": record.robot_uid,
                "name": record.name,
                "blocked": action_type == "stall_autofix"
                or (action_type == "collision_relief" and not self._is_benign_collision_relief(detail))
                or "nav_fail=true" in detail,
                "late_retreat": action_type in {"dead", "death_drop"} or (
                    action_type == "goto_home" and ("hp" in detail or "저하" in detail)
                ),
                "overweight": action_type == "inventory_keep" and "weight=" in detail,
            },
        )

    def _classify_action(self, record: RobotActionRecord) -> tuple[str | None, float, str, str]:
        action_type = record.action_type.lower()
        detail = (record.detail or "").lower()
        if action_type == "aia_control":
            action = self._extract_aia_control_action(detail)
            return action, 1.0, "success", "aia_control"
        if action_type == "aia_decide":
            return "DECIDE", 0.15, "partial", "aia_decision"
        if action_type in {"hunt_nav", "distributed_home", "spawn_disperse", "safe_zone_escape"}:
            return "MOVE", 0.6, "success", "navigation"
        if action_type == "collision_relief" and self._is_benign_collision_relief(detail):
            return "MOVE", 0.45, "success", "navigation"
        if action_type in {"stall_autofix", "collision_relief"}:
            return "MOVE", -0.6, "partial", "navigation_issue"
        if action_type in {"infinite_supply", "inventory_seed", "hp_item_use"}:
            return "USE_ITEM", 0.8, "success", "inventory"
        if action_type in {"shop_supply", "inventory_keep"}:
            return "USE_ITEM", -0.4, "partial", "inventory_issue"
        if action_type in {"robot_chat", "robot_combat_chat"}:
            return "TALK", 0.35, "success", "talk"
        if action_type == "dead":
            return "SURVIVE", -2.0, "failure", "survival"
        if action_type == "death_drop":
            if detail.startswith("disabled:item_discard_removed"):
                return None, 0.0, "partial", "survival"
            return "SURVIVE", -1.0, "failure", "survival"
        if action_type in {"respawn", "goto_home"}:
            return "RETREAT", -0.2 if "hp" in detail or "저하" in detail else 0.1, "partial", "survival"
        if action_type in {"growth_level", "learning_local", "learning_evolution"}:
            return "GROWTH", 1.2, "success", "growth"
        if action_type in {"party_assist", "clan_assist", "support_user", "siege_move"}:
            return "SUPPORT", 0.9, "success", "group"
        return None, 0.0, "partial", "unknown"

    def _extract_aia_control_action(self, detail: str) -> str:
        if detail.startswith("move:"):
            return "MOVE"
        if detail.startswith("attack:"):
            return "ATTACK"
        if detail.startswith("use_skill:") or "heal_" in detail:
            return "USE_SKILL"
        if detail.startswith("retreat:"):
            return "RETREAT"
        if detail.startswith("pickup:"):
            return "PICKUP"
        return "AIA_CONTROL"

    def _detect_issues(self, record: RobotActionRecord) -> list[dict[str, Any]]:
        action_type = record.action_type.lower()
        detail = (record.detail or "").strip()
        issues: list[dict[str, Any]] = []
        if action_type == "shop_supply":
            issues.append(self._issue(record, "item_supply_fallback", "medium", "로봇이 전용 무한 보급 대신 상점 보급 루틴을 사용했습니다."))
        if action_type == "stall_autofix" or (
            action_type == "collision_relief" and not self._is_benign_collision_relief(detail)
        ):
            issues.append(self._issue(record, "movement_stall", "medium", "이동/충돌 자동수정이 발생했습니다. 반복 좌표와 네비게이션을 확인해야 합니다."))
        if action_type in {"runtime_exception", "weapon_equip_error"}:
            issues.append(self._issue(record, "runtime_exception", "high", "서버 런타임 예외 또는 장비 처리 예외가 발생했습니다. AIA/서버 계약과 아이템 상태를 확인해야 합니다."))
        if action_type == "dead":
            issues.append(self._issue(record, "survival_failure", "high", "로봇 사망 또는 사망 드롭 관련 기록이 발생했습니다."))
        if action_type == "death_drop" and not detail.lower().startswith("disabled:item_discard_removed"):
            issues.append(self._issue(record, "survival_failure", "high", "로봇 사망 드롭 관련 비정상 기록이 발생했습니다."))
        if action_type == "goto_home" and ("hp" in detail.lower() or "저하" in detail) and "town_recovery" not in detail.lower():
            issues.append(self._issue(record, "retreat_pressure", "medium", "HP 저하 귀환이 마을/혈맹 복귀 좌표가 아닌 필드 홈으로 처리되었습니다."))
        if action_type == "aia_decide" and "fallback" in detail.lower():
            issues.append(self._issue(record, "aia_fallback", "high", "AIA 판단이 fallback으로 내려갔습니다. 정책/상태 입력을 확인해야 합니다."))
        if action_type == "aia_decide" and self._extract_confidence(detail) < 0.35:
            issues.append(self._issue(record, "low_confidence_decision", "medium", "AIA 판단 신뢰도가 낮습니다. 상태 입력과 정책 편향을 점검해야 합니다."))
        if action_type == "hp_item_use" and "kind=finite" in detail.lower():
            issues.append(self._issue(record, "finite_hp_item_used", "medium", "무한 회복 아이템 대신 유한 회복 아이템이 사용되었습니다."))
        if action_type in {"robot_chat", "robot_combat_chat"}:
            message = detail.split("|", 1)[-1].strip()
            if not message:
                issues.append(self._issue(record, "empty_talk", "medium", "로봇 토크 메시지가 비어 있습니다."))
        return issues

    def _is_benign_collision_relief(self, detail: str) -> bool:
        lowered = (detail or "").lower()
        return any(
            token in lowered
            for token in (
                "밀집",
                "과밀",
                "유저 양보",
                "우회",
                "경로",
                "crowd",
                "crowded",
                "density",
                "relief",
                "reroute",
                "blocked_path",
            )
        )

    def _issue(self, record: RobotActionRecord, issue_type: str, severity: str, message: str) -> dict[str, Any]:
        return {
            "agent_id": record.agent_id,
            "robot_uid": record.robot_uid,
            "object_id": record.object_id,
            "name": record.name or "",
            "issue_type": issue_type,
            "severity": severity,
            "message": message,
            "source_action": record.action_type,
            "source_uid": record.uid,
            "detail": record.detail or "",
            "loc_x": record.loc_x,
            "loc_y": record.loc_y,
            "loc_map": record.loc_map,
        }

    def _apply_talk_memory(self, memory: RobotTalkMemoryRecord) -> bool:
        if not (memory.last_message or "").strip():
            return False
        state = store.get_learning_state(memory.agent_id) or {}
        talk_stats = state.get("talk_stats", {})
        topic = (memory.recent_topic or "일반").strip() or "일반"
        tone = (memory.tone or "중립").strip() or "중립"
        topic_stat = talk_stats.get(topic, {"count": 0, "familiarity_sum": 0, "tones": {}})
        topic_stat["count"] = int(topic_stat.get("count", 0)) + max(1, memory.conversation_count)
        topic_stat["familiarity_sum"] = int(topic_stat.get("familiarity_sum", 0)) + memory.familiarity
        tones = topic_stat.get("tones", {})
        tones[tone] = int(tones.get(tone, 0)) + 1
        topic_stat["tones"] = tones
        talk_stats[topic] = topic_stat
        state["talk_stats"] = talk_stats
        state["last_talk_memory"] = memory.model_dump()
        state["preferred_talk_topic"] = max(talk_stats.items(), key=lambda item: item[1].get("count", 0))[0]
        store.save_learning_state(memory.agent_id, state)
        return True

    def _talk_delete_key(self, memory: RobotTalkMemoryRecord) -> dict[str, Any]:
        return {
            "robot_uid": memory.robot_uid,
            "target_name": memory.target_name or "",
            "target_kind": memory.target_kind or "pc",
        }

    def _detect_talk_memory_issues(self, memory: RobotTalkMemoryRecord) -> list[dict[str, Any]]:
        message = (memory.last_message or "").strip()
        issues: list[dict[str, Any]] = []
        if not message:
            issues.append({
                "agent_id": memory.agent_id,
                "robot_uid": memory.robot_uid,
                "object_id": 0,
                "name": memory.target_name or "",
                "issue_type": "empty_talk_memory",
                "severity": "medium",
                "message": "토크메모리 last_message가 비어 있습니다.",
                "source_action": "talk_memory",
                "source_uid": 0,
                "detail": memory.recent_topic or "",
                "loc_x": 0,
                "loc_y": 0,
                "loc_map": 0,
            })
        if memory.conversation_count > 20 and memory.familiarity < 5:
            issues.append({
                "agent_id": memory.agent_id,
                "robot_uid": memory.robot_uid,
                "object_id": 0,
                "name": memory.target_name or "",
                "issue_type": "talk_relationship_stagnation",
                "severity": "low",
                "message": "대화 횟수 대비 친밀도 성장이 낮습니다.",
                "source_action": "talk_memory",
                "source_uid": 0,
                "detail": memory.recent_topic or "",
                "loc_x": 0,
                "loc_y": 0,
                "loc_map": 0,
            })
        return issues

    def _extract_confidence(self, detail: str) -> float:
        lowered = (detail or "").lower()
        marker = "confidence="
        if marker not in lowered:
            return 1.0
        raw = lowered.split(marker, 1)[1].split("|", 1)[0].strip()
        try:
            return float(raw)
        except Exception:
            return 1.0

    def _merge_counts(self, previous: dict[str, int], update: Counter[str]) -> dict[str, int]:
        merged = defaultdict(int)
        for key, value in (previous or {}).items():
            merged[str(key)] += int(value)
        for key, value in update.items():
            merged[str(key)] += int(value)
        return dict(sorted(merged.items(), key=lambda item: item[1], reverse=True)[:40])

    def _estimate_learning_agents(self) -> int:
        if hasattr(store, "list_learning_ids"):
            try:
                return len([agent_id for agent_id in store.list_learning_ids() if not str(agent_id).startswith(("growth::", "autogrowth::", "automation::", "group::"))])
            except Exception:
                return 0
        return 0


robot_learning_digest_service = RobotLearningDigestService()
