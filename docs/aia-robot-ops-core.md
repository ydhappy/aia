# AIA Robot Ops Core

이 문서는 로봇 + AI + API + Talk + 학습 + 성장 + 운영관리를 AIA 중심으로 운영하기 위한 최소 계약입니다.

## Server Minimal Contract

게임 서버는 아래 역할만 유지합니다.

- 센서 스냅샷 전송: hp, mp, 좌표, 맵, 타겟, 주변 몬스터 레벨, 안전지대, 인벤토리, 위험 핫스팟.
- 최종 실행 검증: 이동 가능 타일, 맵 일치, 안전지대 전투 금지, 타겟 생존/거리.
- 실제 실행: 이동, 공격, 스킬/아이템 사용, 귀환, DB flush.
- 실제 로봇 객체/캐릭터 생성, 삭제, 월드 despawn, DB 캐릭터 테이블 정리.

AIA는 아래 역할을 소유합니다.

- 정책 판단, 위험도 판정, 네비게이션 전략, 분산 사냥, 텔포사냥 힌트.
- 토크, 학습, 성장, 이슈 체크리스트, 운영 대시보드.
- 다른 서버에서도 사용할 수 있는 `/api/v1/robot/ops-tick` 단일 운영 API.
- 서버 로봇북/토크 DB가 비어 있어도 AIA 기본 기준으로 사냥터/토크를 생성.
- 로봇 profile/state/event/trace/learning cache의 AIA 내부 CRUD.

## Robot Spawn Request Bridge

로봇 없는 서버에 바로 붙일 때는 AIA가 서버 원본 `robot` 테이블에 직접 insert하지 않고, 안전한 요청 큐에 생성 요청을 넣습니다.

- DB: `sql/aia_robot_spawn_request_mysql55.sql`
- AIA seed script: `scripts/seed_robot_spawn_requests_mysql55.py`
- Java 8 poller: `integration/java8/AiaRobotSpawnPoller.java`
- Java 8 adapter: `integration/java8/AiaRobotSpawnAdapter.java`
- Java 8 DTO: `integration/java8/AiaRobotSpawnRequest.java`
- Example: `integration/java8/AiaRobotSpawnExample.java`

권장 적용 순서:

1. 게임 DB에 `sql/aia_robot_spawn_request_mysql55.sql` 적용.
2. AIA에서 `scripts/seed_robot_spawn_requests_mysql55.py` 실행해 `pending` 생성 요청 적재.
3. 게임서버 시작 루틴에서 `AiaRobotSpawnPoller.runOnce()` 호출.
4. 서버별 `AiaRobotSpawnAdapter.createAndSpawn()` 안에 기존 `IdFactory`, robot DB insert, inventory/skill 지급, world spawn 로직 연결.
5. 생성 성공 후 poller가 AIA `/robot/profile`에 자동 등록하고 요청 row를 `done`으로 변경.

운영/복구 API:

- JSON: `GET /dashboard/robot-spawn-queue?status=failed`
- GUI: `GET /dashboard/robot-spawn-queue/gui?status=failed`
- 실패 재시도: `POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50`
- 오래된 claimed 복구: `POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50`

이 방식은 서버에 별도 설정 파일을 만들지 않고, AIA가 생성 계획을 DB 큐로 제공하며, 실제 객체 생성은 게임서버가 담당하게 합니다.

## Robot CRUD Contract

AIA의 로봇 CRUD는 게임 서버의 실제 캐릭터 테이블을 직접 수정하지 않습니다. AIA 내부 판단에 필요한 profile, 마지막 state, 최근 event, trace, learning state만 관리합니다.

주요 API:

- `GET /robot`: AIA가 알고 있는 `agent_id` 목록 조회.
- `POST /robot/profile`: 로봇 프로필 생성 또는 저장.
- `PUT /robot/{agent_id}/profile`: 경로의 `agent_id` 기준으로 전체 프로필 교체.
- `PATCH /robot/{agent_id}/profile`: 일부 프로필 필드 수정.
- `GET /robot/{agent_id}`: profile, recent events, last state 조회.
- `DELETE /robot/{agent_id}`: AIA 내부 state/profile/events/trace/learning 삭제.

없는 로봇에 대해 `GET /robot/{agent_id}`, `PATCH /robot/{agent_id}/profile`, `DELETE /robot/{agent_id}`를 호출하면 `404`와 `robot_not_found`를 반환합니다.

게임 서버 권장 순서:

1. 생성: 서버 DB/월드 객체 생성 → `POST /robot/profile` → 첫 tick에서 `POST /api/v1/robot/ops-tick` 또는 `/observe` 전송.
2. 수정: 일부 수정은 `PATCH /robot/{agent_id}/profile`, 전체 재동기화는 `PUT /robot/{agent_id}/profile` 사용.
3. 삭제: 서버 월드에서 despawn/offline 처리 → `DELETE /robot/{agent_id}` → 서버 DB 캐릭터/로봇 테이블 삭제 또는 비활성화.

DB bridge 삭제 정책:

- `DELETE /robot/{agent_id}`는 AIA 런타임 store만 삭제합니다.
- `aia_robot_state`, `aia_robot_event`, `aia_robot_feedback`, `aia_robot_decision`, `aia_robot_trace_summary` 같은 DB bridge 테이블은 자동 삭제하지 않습니다.
- 서버 원본 `robot`, `robot_clan`, `robot_setting` 테이블은 AIA가 절대 삭제하지 않습니다.
- 운영자가 `aia_*` 행을 정리할 경우 백업 후 수동 purge 또는 별도 유지보수 스크립트로 처리합니다.

UTF-8 / MySQL 5.5 정책:

- HTTP JSON은 UTF-8 기준입니다.
- Redis store는 JSON 저장 시 `ensure_ascii=false` 정책을 사용합니다.
- DB bridge JSON 저장도 `ensure_ascii=false` 정책을 사용합니다.
- MySQL 5.5 호환을 위해 SQL 기본 charset은 `utf8`을 사용합니다.
- Java 연동부는 `Content-Type: application/json; charset=utf-8`, 로그/파일/DB는 UTF-8을 권장합니다.

관련 회귀 테스트:

```bash
pytest tests/test_robot_crud_api.py
pytest tests/test_spawn_request_dashboard.py
```

AIA 실행 후 HTTP smoke:

```bash
python scripts/robot_crud_smoke.py
```

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
- `hunt_zone`: DB 로봇북이 없을 때 AIA가 선택한 운영자 편집 가능 사냥 기준.
- `talk_suggestion`: DB 토크 테이블이 없어도 AIA가 만든 현재 상황 대화 힌트.

## DB-Less Autonomy Baseline

운영자 편집 파일: `app/config/robot_autonomy_defaults.json`

이 파일에서 기본 사냥터, 클래스별 역할/성향, 토크 문구를 수정할 수 있습니다. 서버 DB의 로봇북이나 토크 테이블이 비어 있어도 AIA는 이 파일을 기준으로 임시 프로필, 순찰 좌표, 말투를 생성합니다.

- 조회: `GET /dashboard/robot-autonomy-baseline`
- 저장: `POST /dashboard/robot-autonomy-baseline`
- 리로드: `POST /dashboard/robot-autonomy-baseline/reload`

학습 digest가 성공하면 응답은 `delete_uids`와 `delete_talk_keys`를 내려줍니다. 서버는 학습 반영이 끝난 `aia_robot_event` 실시간 기록을 삭제하고, `aia_robot_issue`는 해결 확인 전까지 보존합니다.

## Dashboard

- JSON: `GET /dashboard/robot-ai`
- GUI: `GET /dashboard/robot-ai/gui`
- Spawn Queue JSON: `GET /dashboard/robot-spawn-queue`
- Spawn Queue GUI: `GET /dashboard/robot-spawn-queue/gui`

대시보드는 AIA 의존도, 체크리스트, 품질 게이트, 네비게이션 계약, 학습 이슈, spawn queue 처리 상태를 제공합니다.

## Required Gates

- Python: `python -m compileall -q app scripts integration tests`
- Robot CRUD API test: `pytest tests/test_robot_crud_api.py`
- Spawn Queue dashboard test: `pytest tests/test_spawn_request_dashboard.py`
- Tests: `pytest`
- Dependencies: `pip check`
- Java 8 integration sample: `javac -encoding UTF-8 integration/java8/*.java`
- Windows one-shot: `powershell -ExecutionPolicy Bypass -File scripts/run_quality_gates.ps1`
- Ops tick HTTP smoke: run AIA, then `python scripts/ops_tick_smoke.py`
- Robot CRUD HTTP smoke: run AIA, then `python scripts/robot_crud_smoke.py`

배포 전에는 runtime issue count, fallback rate, dashboard warning을 0에 가깝게 유지해야 합니다.

## Runtime Adapters

- Python: `examples/python_client.py`, `scripts/ops_tick_smoke.py`, `scripts/robot_crud_smoke.py`, `scripts/seed_robot_spawn_requests_mysql55.py`
- Java 8: `integration/java8/LocalAiaClient.java`, `integration/java8/AiaDecisionParser.java`, `integration/java8/RobotCrudExample.java`, `integration/java8/AiaRobotSpawnPoller.java`, `integration/java8/AiaRobotSpawnAdapter.java`
- Jython 2.7: `integration/jython/aia_ops_tick_client.py`
- Script: `scripts/run_quality_gates.ps1`
