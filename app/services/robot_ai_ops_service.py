from __future__ import annotations

from html import escape
from typing import Any

from app.models.dashboard_models import RobotAiChecklistItem, RobotAiOpsDashboardResponse
from app.models.request_models import AgentState
from app.services.store_factory import store


NAVIGATION_ALGORITHMS = [
    "monster_track",
    "spawn_anchor",
    "frontier_roam",
    "party_rally",
    "teleport_hunt",
    "safe_zone_exit",
    "danger_retreat",
    "pc_auto_hunt_sync",
]


class RobotAiOpsService:
    """AIA 중심 로봇 운영 코어.

    서버는 센서값과 최종 실행 검증만 맡고, 위험도/네비전략/운영 체크는 AIA가 담당한다.
    """

    def assess_state(self, state: AgentState) -> dict[str, Any]:
        extras = state.extras or {}
        robot_level = self._to_int(extras.get("robot_level", extras.get("level", 1)), 1)
        local_area_level = self._to_int(extras.get("local_area_level"), 0)
        target_level = self._to_int(extras.get("target_level"), 0)
        nearby_max_level = self._to_int(extras.get("nearby_monster_max_level"), 0)
        stuck_ms = self._to_int(extras.get("stuck_ms"), 0)
        danger_hotspot = self._to_bool(extras.get("danger_hotspot"))
        nav_fail_count = self._to_int(extras.get("nav_fail_count"), 0)
        actor_kind = str(extras.get("actor_kind") or "robot")

        risk_score = 0
        reasons: list[str] = []

        if state.must_use_hp_item:
            risk_score += 18
            reasons.append("hp_item_required")
        if state.hp <= 30:
            risk_score += 38
            reasons.append("critical_hp")
        if danger_hotspot:
            risk_score += 36
            reasons.append("danger_hotspot")
        if local_area_level > 0:
            over = local_area_level - (robot_level + self._safe_level_gap(robot_level))
            if over > 0:
                risk_score += min(42, 16 + over * 7)
                reasons.append(f"local_area_over_level:{local_area_level}")
        if target_level > 0:
            over = target_level - (robot_level + self._safe_level_gap(robot_level))
            if over > 0:
                risk_score += min(36, 12 + over * 6)
                reasons.append(f"target_over_level:{target_level}")
        if nearby_max_level > 0:
            over = nearby_max_level - (robot_level + self._safe_level_gap(robot_level) + 2)
            if over > 0:
                risk_score += min(28, 8 + over * 4)
                reasons.append(f"nearby_over_level:{nearby_max_level}")
        if stuck_ms >= 15000:
            risk_score += 24
            reasons.append("movement_stall")
        if nav_fail_count >= 3:
            risk_score += 18
            reasons.append("navigation_failures")
        if state.weight_percent is not None and state.weight_percent >= 85:
            risk_score += 16
            reasons.append("overweight")

        severity = "high" if risk_score >= 55 else "medium" if risk_score >= 28 else "low"
        return {
            "actor_kind": actor_kind,
            "robot_level": robot_level,
            "local_area_level": local_area_level,
            "target_level": target_level,
            "nearby_monster_max_level": nearby_max_level,
            "danger_hotspot": danger_hotspot,
            "risk_score": min(100, risk_score),
            "severity": severity,
            "reasons": reasons,
            "should_retreat": severity == "high" and not state.safe_zone,
            "should_reposition": severity == "medium" and not state.safe_zone,
        }

    def choose_navigation(
        self,
        state: AgentState,
        profile: dict[str, Any] | None = None,
        learning_state: dict[str, Any] | None = None,
        runtime_bias: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        profile = profile or {}
        learning_state = learning_state or {}
        runtime_bias = runtime_bias or {}
        assessment = self.assess_state(state)
        extras = state.extras or {}
        actor_kind = assessment["actor_kind"]
        role = str(profile.get("role") or extras.get("role_mode") or "custom")
        group_mode = str(extras.get("hunt_group_mode") or profile.get("group_mode") or "")
        preferred_algorithm = str(runtime_bias.get("nav_algorithm") or learning_state.get("preferred_nav_algorithm") or "")

        if assessment["should_retreat"]:
            algorithm = "danger_retreat"
            mode = "teleport" if state.can_teleport else "safe_zone"
            reason = "risk_assessment_high"
        elif state.safe_zone:
            algorithm = "safe_zone_exit"
            mode = "patrol"
            reason = "safe_zone_reposition"
        elif actor_kind == "pc_auto_hunt":
            algorithm = "pc_auto_hunt_sync"
            mode = "target_priority"
            reason = "pc_auto_hunt_navigation"
        elif state.target_id and state.target_distance is not None:
            algorithm = "monster_track" if state.target_distance <= 8 else "spawn_anchor"
            mode = "approach" if state.target_distance > 1 else "engage"
            reason = "target_visible"
        elif state.can_teleport and self._to_bool(extras.get("teleport_hunt_enabled")):
            algorithm = "teleport_hunt"
            mode = "teleport_probe"
            reason = "teleport_hunt_enabled"
        elif "파티" in group_mode or "혈맹" in group_mode or role in {"support", "healer", "tank"}:
            algorithm = "party_rally"
            mode = "rally_patrol"
            reason = "group_hunt"
        elif preferred_algorithm in NAVIGATION_ALGORITHMS:
            algorithm = preferred_algorithm
            mode = "learned_route"
            reason = "learning_preferred_algorithm"
        else:
            seed = abs((state.x * 31) + (state.y * 17) + int(state.map_id or 0))
            algorithm = "spawn_anchor" if seed % 3 == 0 else "frontier_roam"
            mode = "wide_patrol" if algorithm == "frontier_roam" else "anchor_sweep"
            reason = "diverse_default"

        return {
            "algorithm": algorithm,
            "mode": mode,
            "reason": reason,
            "risk_score": assessment["risk_score"],
            "severity": assessment["severity"],
            "reasons": assessment["reasons"],
        }

    def dashboard_snapshot(self, agent_ids: list[str] | None = None) -> RobotAiOpsDashboardResponse:
        agent_ids = agent_ids or self._known_agent_ids()
        metrics = store.metrics()
        learning_summary = self._learning_summary()
        active_agents = sum(1 for agent_id in agent_ids if store.get_state(agent_id))
        learning_agents = sum(1 for agent_id in agent_ids if store.get_learning_state(agent_id))
        issue_count = int(learning_summary.get("issue_count", metrics.get("total_learning_issues", 0)) or 0)
        checklist = self.build_checklist(agent_ids, learning_summary, metrics)
        dependency_score = self._dependency_score(checklist)
        return RobotAiOpsDashboardResponse(
            dependency_score=dependency_score,
            total_agents=len(agent_ids),
            active_agents=active_agents,
            learning_agents=learning_agents,
            issue_count=issue_count,
            checklist=checklist,
            navigation_algorithms=NAVIGATION_ALGORITHMS,
            runtime_layers=[
                "python:policy/learning/dashboard",
                "java8:minimal_state_bridge",
                "script:ops_build_test_cycle",
                "jython:optional_adapter_contract",
            ],
            server_minimal_contract={
                "server_keeps": ["sensor_snapshot", "final_path_check", "combat_execution", "db_flush"],
                "aia_owns": ["policy", "navigation_strategy", "talk", "learning", "growth", "issue_checklist", "ops_dashboard"],
                "portable": True,
            },
            metrics=metrics,
            learning_summary=learning_summary,
        )

    def build_checklist(
        self,
        agent_ids: list[str],
        learning_summary: dict[str, Any],
        metrics: dict[str, Any],
    ) -> list[RobotAiChecklistItem]:
        issue_count = int(learning_summary.get("issue_count", metrics.get("total_learning_issues", 0)) or 0)
        recent_issues = learning_summary.get("recent_issues") or []
        total_decide = int(metrics.get("total_decide_requests", 0) or 0)
        total_fallbacks = int(metrics.get("total_fallbacks", 0) or 0)
        fallback_rate = (total_fallbacks / total_decide) if total_decide > 0 else 0.0

        return [
            self._item("bridge", "서버-AIA 브리지", "pass", "low", "observe/decide/profile/event 계약 사용", "서버는 센서와 최종 실행만 유지"),
            self._item("dashboard", "AIA 전용 대시보드", "pass", "low", "/dashboard/robot-ai 및 /dashboard/robot-ai/gui 제공", "운영자는 AIA에서 상태 확인"),
            self._item("navigation", "네비게이션 다양성", "pass", "low", ",".join(NAVIGATION_ALGORITHMS), "상황별 알고리즘 선택"),
            self._item(
                "fallback",
                "AIA fallback 제로화",
                "pass" if fallback_rate <= 0.03 else "warn",
                "medium" if fallback_rate > 0.03 else "low",
                f"fallback_rate={fallback_rate:.2%}",
                "fallback이 증가하면 상태 입력/정책 검증",
            ),
            self._item(
                "issues",
                "이슈 제로화",
                "pass" if issue_count == 0 else "warn",
                "high" if issue_count > 0 else "low",
                f"issue_count={issue_count},recent={len(recent_issues)}",
                "survival/stall/talk/supply/runtime 이슈를 digest로 재학습",
            ),
            self._item(
                "learning",
                "학습/성장 반영",
                "pass" if int(metrics.get("total_learning_digests", 0) or 0) > 0 else "warn",
                "medium",
                f"digests={metrics.get('total_learning_digests', 0)}",
                "서버 종료 전 digest가 누락되지 않도록 확인",
            ),
            self._item(
                "agents",
                "에이전트 상태 수집",
                "pass" if len(agent_ids) == 0 or any(store.get_state(agent_id) for agent_id in agent_ids) else "warn",
                "medium",
                f"known_agents={len(agent_ids)}",
                "다른 서버 적용 시 agent_id 목록 또는 observe 호출 확인",
            ),
        ]

    def render_dashboard_html(self, agent_ids: list[str] | None = None) -> str:
        snapshot = self.dashboard_snapshot(agent_ids)
        checklist_rows = "\n".join(
            f"<tr><td>{escape(item.key)}</td><td>{escape(item.title)}</td><td class='{escape(item.status)}'>{escape(item.status)}</td>"
            f"<td>{escape(item.severity)}</td><td>{escape(item.detail)}</td><td>{escape(item.action)}</td></tr>"
            for item in snapshot.checklist
        )
        algorithms = "".join(f"<li>{escape(name)}</li>" for name in snapshot.navigation_algorithms)
        return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AIA Robot Ops Dashboard</title>
  <style>
    :root {{ --bg:#f4efe4; --ink:#1e2526; --line:#31423f; --good:#1d7d50; --warn:#ad6b00; }}
    body {{ margin:0; font-family: Georgia, 'Noto Serif KR', serif; background: radial-gradient(circle at top left,#fff8dd,var(--bg)); color:var(--ink); }}
    main {{ max-width:1120px; margin:0 auto; padding:34px 20px 54px; }}
    h1 {{ font-size:38px; margin:0 0 8px; letter-spacing:-.03em; }}
    .sub {{ color:#58615f; margin-bottom:26px; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }}
    .card {{ border:2px solid var(--line); border-radius:18px; background:#fffdf4cc; padding:18px; box-shadow:6px 6px 0 #c9b98d; }}
    .num {{ font-size:34px; font-weight:800; }}
    table {{ width:100%; border-collapse:collapse; margin-top:24px; background:#fffdf4cc; }}
    th,td {{ border:1px solid #9c9274; padding:10px; text-align:left; vertical-align:top; }}
    th {{ background:#e7dcc2; }}
    .pass {{ color:var(--good); font-weight:700; }}
    .warn {{ color:var(--warn); font-weight:700; }}
    ul {{ columns:2; background:#fffdf4aa; border:1px solid #9c9274; padding:18px 30px; border-radius:14px; }}
  </style>
</head>
<body>
<main>
  <h1>AIA Robot Ops Dashboard</h1>
  <p class="sub">로봇 + AI + API + Talk + 학습 + 성장 + 운영관리 통합 대시보드</p>
  <section class="cards">
    <div class="card"><div>의존도 점수</div><div class="num">{snapshot.dependency_score}%</div></div>
    <div class="card"><div>전체 에이전트</div><div class="num">{snapshot.total_agents}</div></div>
    <div class="card"><div>활성 에이전트</div><div class="num">{snapshot.active_agents}</div></div>
    <div class="card"><div>이슈</div><div class="num">{snapshot.issue_count}</div></div>
  </section>
  <h2>운영 체크리스트</h2>
  <table><thead><tr><th>키</th><th>항목</th><th>상태</th><th>위험도</th><th>상세</th><th>조치</th></tr></thead><tbody>{checklist_rows}</tbody></table>
  <h2>네비게이션 알고리즘</h2>
  <ul>{algorithms}</ul>
</main>
</body>
</html>"""

    def _known_agent_ids(self) -> list[str]:
        if hasattr(store, "list_agent_ids"):
            try:
                return list(store.list_agent_ids())
            except Exception:
                return []
        return []

    def _learning_summary(self) -> dict[str, Any]:
        try:
            from app.services.robot_learning_digest_service import robot_learning_digest_service

            return robot_learning_digest_service.summary()
        except Exception:
            return {}

    def _dependency_score(self, checklist: list[RobotAiChecklistItem]) -> int:
        if not checklist:
            return 0
        score = 120
        for item in checklist:
            if item.status == "warn":
                score -= 10 if item.severity == "medium" else 18
            elif item.status not in {"pass", "ok"}:
                score -= 14
        return max(0, min(120, score))

    def _item(self, key: str, title: str, status: str, severity: str, detail: str, action: str) -> RobotAiChecklistItem:
        return RobotAiChecklistItem(key=key, title=title, status=status, severity=severity, detail=detail, action=action)

    def _safe_level_gap(self, level: int) -> int:
        if level <= 5:
            return 2
        if level <= 10:
            return 2
        if level <= 20:
            return 4
        if level <= 35:
            return 7
        return 12

    def _to_int(self, value: Any, default: int = 0) -> int:
        try:
            if value is None or value == "":
                return default
            return int(value)
        except Exception:
            return default

    def _to_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "위험", "danger"}


robot_ai_ops_service = RobotAiOpsService()
