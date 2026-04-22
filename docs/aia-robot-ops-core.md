# AIA Robot Ops Core

이 문서는 로봇 + AI + API + Talk + 학습 + 성장 + 운영관리를 AIA 중심으로 운영하기 위한 최소 계약입니다.

## Server Minimal Contract

게임 서버는 아래 역할만 유지합니다.

- 센서 스냅샷 전송: hp, mp, 좌표, 맵, 타겟, 주변 몬스터 레벨, 안전지대, 인벤토리, 위험 핫스팟.
- 최종 실행 검증: 이동 가능 타일, 맵 일치, 안전지대 전투 금지, 타겟 생존/거리.
- 실제 실행: 이동, 공격, 스킬/아이템 사용, 귀환, DB flush.

AIA는 아래 역할을 소유합니다.

- 정책 판단, 위험도 판정, 네비게이션 전략, 분산 사냥, 텔포사냥 힌트.
- 토크, 학습, 성장, 이슈 체크리스트, 운영 대시보드.
- 다른 서버에서도 사용할 수 있는 `/api/v1/robot/ops-tick` 단일 운영 API.

## Ops Tick API

`POST /api/v1/robot/ops-tick`

한 번의 호출로 profile, event, observe, decide, feedback, dashboard 요약을 처리합니다.

```json
{
  "profile": {"agent_id": "robot_1", "role": "custom", "style": "balanced"},
  "observe": {"agent_id": "robot_1", "tick": 1, "state": {"hp": 90, "mp": 20, "x": 33400, "y": 32800, "map_id": 68}},
  "decide": {"agent_id": "robot_1", "tick": 1, "state": {"hp": 90, "mp": 20, "x": 33400, "y": 32800, "map_id": 68}},
  "include_dashboard": true
}
```

응답의 `decide_result.action_args`에는 서버가 바로 검증해서 사용할 수 있는 네비게이션 힌트가 포함됩니다.

- `points`: AIA가 추천하는 후보 좌표 목록.
- `target_x`, `target_y`, `target_map_id`: 1순위 이동 후보.
- `route_id`: 로봇별 분산 route 식별자.
- `spread_radius`: 몰림 방지용 분산 반경.
- `step_budget`: 이번 tick에서 허용할 이동/탐색 강도.
- `server_validation`: 서버가 반드시 검증해야 할 조건.
- `client_server_sync`: 클라-서버 좌표 싱크 원칙.

## Dashboard

- JSON: `GET /dashboard/robot-ai`
- GUI: `GET /dashboard/robot-ai/gui`

대시보드는 AIA 의존도, 체크리스트, 품질 게이트, 네비게이션 계약, 학습 이슈 요약을 제공합니다.

## Required Gates

- Python: `python -m compileall -q app scripts integration tests`
- Tests: `pytest`
- Dependencies: `pip check`
- Java 8 integration sample: `javac integration/java8/*.java`
- Windows one-shot: `powershell -ExecutionPolicy Bypass -File scripts/run_quality_gates.ps1`
- HTTP smoke: run AIA, then `python scripts/ops_tick_smoke.py`

배포 전에는 runtime issue count, fallback rate, dashboard warning을 0에 가깝게 유지해야 합니다.

## Runtime Adapters

- Python: `examples/python_client.py`, `scripts/ops_tick_smoke.py`
- Java 8: `integration/java8/LocalAiaClient.java`, `integration/java8/AiaDecisionParser.java`
- Jython 2.7: `integration/jython/aia_ops_tick_client.py`
- Script: `scripts/run_quality_gates.ps1`
