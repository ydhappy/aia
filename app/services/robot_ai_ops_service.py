from __future__ import annotations

from html import escape
from typing import Any

from app.models.dashboard_models import RobotAiChecklistItem, RobotAiOpsDashboardResponse
from app.models.request_models import AgentState
from app.services.robot_autonomy_baseline_service import robot_autonomy_baseline_service
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
        learning_deaths = self._to_int(extras.get("learning_death_count"), 0)
        learning_caution = self._to_int(extras.get("learning_caution"), 0)
        learning_confidence = self._to_int(extras.get("learning_confidence"), 0)
        recent_death_burst = self._to_int(extras.get("recent_death_burst"), 0)
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
        if recent_death_burst > 0:
            risk_score += 45
            reasons.append(f"recent_death_burst:{recent_death_burst}")
        if learning_deaths >= 3 and learning_caution >= 5:
            risk_score += 56
            reasons.append(f"repeat_death_profile:{learning_deaths}/{learning_caution}")
        elif learning_deaths >= 3:
            risk_score += 16
            reasons.append(f"death_history:{learning_deaths}")
        elif learning_caution >= 6:
            risk_score += 14
            reasons.append(f"caution_profile:{learning_caution}")
        if learning_confidence <= -4:
            risk_score += 12
            reasons.append(f"low_learning_confidence:{learning_confidence}")
        if state.hp <= 70 and (learning_caution >= 5 or learning_deaths >= 3):
            risk_score += 22
            reasons.append("fragile_profile_hp_pressure")

        severity = "high" if risk_score >= 55 else "medium" if risk_score >= 28 else "low"
        return {
            "actor_kind": actor_kind,
            "robot_level": robot_level,
            "local_area_level": local_area_level,
            "target_level": target_level,
            "nearby_monster_max_level": nearby_max_level,
            "danger_hotspot": danger_hotspot,
            "learning_death_count": learning_deaths,
            "learning_caution": learning_caution,
            "learning_confidence": learning_confidence,
            "recent_death_burst": recent_death_burst,
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
        agent_id: str = "",
    ) -> dict[str, Any]:
        learning_state = learning_state or {}
        runtime_bias = runtime_bias or {}
        profile = robot_autonomy_baseline_service.resolve_profile(agent_id, state, profile or {}, learning_state)
        assessment = self.assess_state(state)
        extras = state.extras or {}
        hunt_zone = robot_autonomy_baseline_service.select_hunt_zone(state, profile, learning_state)
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

        points = self._navigation_points(state, profile, algorithm)
        primary_point = points[0] if points else {}
        return {
            "algorithm": algorithm,
            "mode": mode,
            "reason": reason,
            "risk_score": assessment["risk_score"],
            "severity": assessment["severity"],
            "reasons": assessment["reasons"],
            "points": points,
            "target_x": primary_point.get("x"),
            "target_y": primary_point.get("y"),
            "target_map_id": primary_point.get("map_id", state.map_id),
            "spread_radius": self._spread_radius(assessment["robot_level"], algorithm),
            "step_budget": self._step_budget(algorithm, assessment["severity"]),
            "route_id": self._route_id(state, algorithm),
            "hunt_zone": hunt_zone,
            "autonomy_source": "aia_default_baseline",
            "operator_profile": {
                "editable_config": str(robot_autonomy_baseline_service.config_path),
                "no_robot_book_required": True,
                "no_talk_table_required": True,
            },
            "server_validation": {
                "authoritative": "server",
                "requires_passable_tile": True,
                "requires_map_match": True,
                "reject_safe_zone_combat": True,
            },
            "client_server_sync": {
                "coordinate_source": "server_sensor",
                "aia_is_strategy_owner": True,
                "server_is_execution_owner": True,
                "map_id": state.map_id,
            },
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
            navigation_contract=self.navigation_contract(),
            quality_gates=self.quality_gates(checklist, metrics, learning_summary),
            metrics=metrics,
            learning_summary=learning_summary,
            autonomy_baseline=robot_autonomy_baseline_service.operator_view(),
            cleanup_policy=robot_autonomy_baseline_service.cleanup_policy(),
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
                "aia_default_baseline",
                "DB 없는 기본 로봇 기준",
                "pass",
                "low",
                "로봇북/토크 테이블이 비어도 AIA JSON 기준으로 사냥터와 말투 생성",
                "운영자는 robot_autonomy_defaults.json 또는 대시보드 API로 변경",
            ),
            self._item(
                "log_cleanup",
                "학습 후 실시간 로그 정리",
                "pass",
                "low",
                "digest 성공 시 action log와 학습 완료 talk memory 삭제 키 반환",
                "issue log는 해결 확인 전까지 보존",
            ),
            self._item(
                "server_client_sync",
                "서버-클라 좌표 싱크",
                "pass",
                "low",
                "AIA points/target/map + server final validation 계약",
                "서버는 passable/map/safe-zone 검증 후 실행",
            ),
            self._item(
                "portable_ops_tick",
                "타 서버 즉시 적용 API",
                "pass",
                "low",
                "/api/v1/robot/ops-tick 단일 운영 tick 계약",
                "다른 서버는 observe/decide/profile/event를 한 번에 연동",
            ),
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
                "pass" if issue_count == 0 else "warn",
                "medium" if issue_count == 0 else "high",
                f"digests={metrics.get('total_learning_digests', 0)},issues={issue_count}",
                "digest 미실행은 준비 상태, issue 발생 시 우선 반영",
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

    def navigation_contract(self) -> dict[str, Any]:
        return {
            "aia_outputs": [
                "nav_algorithm",
                "nav_reason",
                "risk_score",
                "risk_severity",
                "points",
                "target_x",
                "target_y",
                "target_map_id",
                "spread_radius",
                "step_budget",
                "route_id",
            ],
            "server_must_validate": ["map_match", "passable_tile", "safe_zone_rule", "target_alive", "range"],
            "client_sync_rule": "server_coordinates_are_authoritative_aia_routes_are_hints",
            "anti_clump_rule": "route_id_and_spread_radius_seed_each_robot_differently",
            "bookless_rule": "if robot_book is empty AIA selects operator-editable hunt_zones or current-position generated zone",
        }

    def quality_gates(
        self,
        checklist: list[RobotAiChecklistItem],
        metrics: dict[str, Any],
        learning_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        total_decide = int(metrics.get("total_decide_requests", 0) or 0)
        total_fallbacks = int(metrics.get("total_fallbacks", 0) or 0)
        fallback_rate = (total_fallbacks / total_decide) if total_decide > 0 else 0.0
        issue_count = int(learning_summary.get("issue_count", metrics.get("total_learning_issues", 0)) or 0)
        warn_count = sum(1 for item in checklist if item.status == "warn")
        return [
            {
                "key": "compile",
                "status": "required",
                "target": "python compileall + java8 javac",
                "action": "배포 전마다 전체 컴파일 수행",
            },
            {
                "key": "runtime",
                "status": "pass" if issue_count == 0 else "warn",
                "target": "runtime issue_count == 0",
                "actual": issue_count,
                "action": "digest issue를 학습 반영 후 재검증",
            },
            {
                "key": "fallback",
                "status": "pass" if fallback_rate <= 0.03 else "warn",
                "target": "fallback_rate <= 3%",
                "actual": round(fallback_rate, 4),
                "action": "fallback 원인 trace 확인",
            },
            {
                "key": "dashboard",
                "status": "pass" if warn_count == 0 else "warn",
                "target": "checklist warn == 0",
                "actual": warn_count,
                "action": "대시보드 warn 항목부터 수정",
            },
        ]

    def render_dashboard_html(self, agent_ids: list[str] | None = None) -> str:
        snapshot = self.dashboard_snapshot(agent_ids)
        checklist_rows = "\n".join(
            f"<tr><td>{escape(item.key)}</td><td>{escape(item.title)}</td><td class='{escape(item.status)}'>{escape(item.status)}</td>"
            f"<td>{escape(item.severity)}</td><td>{escape(item.detail)}</td><td>{escape(item.action)}</td></tr>"
            for item in snapshot.checklist
        )
        gate_rows = "\n".join(
            f"<tr><td>{escape(str(item.get('key', '')))}</td><td class='{escape(str(item.get('status', '')))}'>{escape(str(item.get('status', '')))}</td>"
            f"<td>{escape(str(item.get('target', '')))}</td><td>{escape(str(item.get('actual', '')))}</td><td>{escape(str(item.get('action', '')))}</td></tr>"
            for item in snapshot.quality_gates
        )
        algorithms = "".join(f"<li>{escape(name)}</li>" for name in snapshot.navigation_algorithms)
        baseline = snapshot.autonomy_baseline.get("summary", {})
        cleanup = snapshot.cleanup_policy
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
  <h2>품질 게이트</h2>
  <table><thead><tr><th>키</th><th>상태</th><th>목표</th><th>현재</th><th>조치</th></tr></thead><tbody>{gate_rows}</tbody></table>
  <h2>DB 없는 AIA 기준</h2>
  <table><tbody>
    <tr><th>운영자 설정</th><td>{escape(str(snapshot.autonomy_baseline.get('config_path', '')))}</td></tr>
    <tr><th>사냥구역</th><td>{escape(str(baseline.get('hunt_zones', 0)))}</td></tr>
    <tr><th>클래스 기준</th><td>{escape(str(baseline.get('class_profiles', 0)))}</td></tr>
    <tr><th>토크 주제</th><td>{escape(str(baseline.get('talk_topics', 0)))}</td></tr>
    <tr><th>로그정리</th><td>{escape(str(cleanup))}</td></tr>
  </tbody></table>
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

    def _navigation_points(self, state: AgentState, profile: dict[str, Any], algorithm: str) -> list[dict[str, int]]:
        if state.map_id is None:
            return []
        extras = state.extras or {}
        level = self._to_int(extras.get("robot_level", extras.get("level", 1)), 1)
        radius = self._spread_radius(level, algorithm)
        base_x = self._to_int(profile.get("home_x", extras.get("home_x")), state.x)
        base_y = self._to_int(profile.get("home_y", extras.get("home_y")), state.y)
        if algorithm in {"frontier_roam", "monster_track", "teleport_hunt", "pc_auto_hunt_sync"}:
            base_x = state.x
            base_y = state.y
        seed = self._seed(state, algorithm)
        vectors = [
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1),
            (1, 1),
            (-1, 1),
            (-1, -1),
            (1, -1),
        ]
        points: list[dict[str, int]] = []
        for index in range(3):
            dx, dy = vectors[(seed + index * 3) % len(vectors)]
            spread = radius + ((seed // (index + 1)) % max(3, radius // 2))
            points.append({
                "x": base_x + dx * spread,
                "y": base_y + dy * spread,
                "map_id": int(state.map_id),
                "weight": 100 - index * 15,
            })
        return points

    def _spread_radius(self, level: int, algorithm: str) -> int:
        base = 10
        if level <= 10:
            base = 7
        elif level <= 25:
            base = 12
        elif level <= 45:
            base = 18
        else:
            base = 24
        if algorithm == "frontier_roam":
            return base + 10
        if algorithm == "spawn_anchor":
            return base + 6
        if algorithm == "party_rally":
            return max(6, base - 4)
        if algorithm == "teleport_hunt":
            return base + 14
        return base

    def _step_budget(self, algorithm: str, severity: str) -> int:
        if severity == "high":
            return 1
        if algorithm in {"teleport_hunt", "frontier_roam"}:
            return 5
        if algorithm in {"spawn_anchor", "party_rally"}:
            return 4
        return 3

    def _route_id(self, state: AgentState, algorithm: str) -> str:
        return f"{state.map_id or 0}:{algorithm}:{self._seed(state, algorithm) % 997}"

    def _seed(self, state: AgentState, algorithm: str) -> int:
        raw = f"{algorithm}:{state.x}:{state.y}:{state.map_id}:{state.extras.get('robot_uid', '') if state.extras else ''}"
        seed = 0
        for ch in raw:
            seed = (seed * 131 + ord(ch)) & 0x7FFFFFFF
        return seed


robot_ai_ops_service = RobotAiOpsService()
