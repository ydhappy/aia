# SQLite DB Bridge

## 목적
AIA를 가장 쉽게 테스트하거나 공용 예제로 배포할 수 있도록 SQLite 기반 DB bridge를 제공합니다.

## 설정
- `DB_BRIDGE_BACKEND=sqlite`
- `DB_BRIDGE_SQLITE_PATH=./aia_bridge.db`

## 자동 생성 테이블
- `robot_state`
- `robot_event`
- `robot_feedback`
- `robot_decision`
- `robot_trace_summary`

## 사용 API
- `GET /db-bridge/states`
- `GET /db-bridge/events`
- `GET /db-bridge/feedback`
- `POST /db-bridge/decision`
- `POST /db-bridge/trace`

## 권장 용도
- 빠른 테스트
- 단일 인스턴스 운영
- 공용 데모

## 주의점
- 대규모 운영에서는 PostgreSQL/MySQL 같은 외부 DB로 확장하는 것이 더 적합합니다.
- SQLite는 시작점으로는 매우 좋지만, 대규모 다중 writer 환경에는 제한이 있습니다.
