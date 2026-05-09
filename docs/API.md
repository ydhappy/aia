# AIA API 요약

## 기본

```http
GET /health
GET /health/details
GET /metrics
```

`/health`는 가벼운 생존 확인입니다.

`/health/details`는 LLM, state store, DB bridge backend, 선택형 MySQL 연결 상태, 필수 AIA 테이블 존재 여부를 함께 보여줍니다.

MySQL 상세 응답 예:

```json
{
  "mysql": {
    "enabled": true,
    "status": "ok",
    "missing_tables": [],
    "tables": {
      "aia_robot_spawn_request": {
        "exists": true,
        "required_sql": "sql/aia_robot_spawn_request_mysql55.sql"
      },
      "aia_robot_state": {
        "exists": true,
        "required_sql": "sql/aia_robot_schema.sql"
      },
      "aia_robot_event": {
        "exists": true,
        "required_sql": "sql/aia_robot_schema.sql"
      },
      "aia_robot_feedback": {
        "exists": true,
        "required_sql": "sql/aia_robot_schema.sql"
      },
      "aia_robot_decision": {
        "exists": true,
        "required_sql": "sql/aia_robot_schema.sql"
      },
      "aia_robot_trace_summary": {
        "exists": true,
        "required_sql": "sql/aia_robot_schema.sql"
      }
    }
  }
}
```

## 판단

```http
POST /observe
POST /decide
POST /api/v1/robot/sync
POST /api/v1/robot/ops-tick
```

권장 통합 API는 다음입니다.

```http
POST /api/v1/robot/ops-tick
```

## 로봇 CRUD

```http
GET    /robot
POST   /robot/profile
PUT    /robot/{agent_id}/profile
PATCH  /robot/{agent_id}/profile
GET    /robot/{agent_id}
DELETE /robot/{agent_id}
```

`DELETE /robot/{agent_id}`는 AIA 내부 runtime store만 삭제합니다. 서버 원본 로봇 DB와 월드 객체는 게임서버가 정리해야 합니다.

## 로봇 생성 요청 큐

```http
POST /robot/spawn-requests
```

예시:

```json
{
  "server_name": "main",
  "count": 30,
  "classes": ["knight", "elf", "wizard"],
  "level_min": 1,
  "level_max": 30
}
```

응답 주요 필드:

```text
accepted
created
submitted
affected
duplicate_policy
required_table
requests
```

## Spawn Queue 대시보드

```http
GET /dashboard/robot-spawn-queue
GET /dashboard/robot-spawn-queue/gui
GET /dashboard/robot-spawn-queue?status=failed
GET /dashboard/robot-spawn-queue/gui?status=failed
```

응답 주요 필드:

```text
enabled
reason
operator_hint
status_filter
counts
total
needs_attention
recent
```

복구 API:

```http
POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

## 로봇 이벤트/학습

```http
POST /robot/event
POST /robot/feedback
GET  /robot/{agent_id}/trace
GET  /robot/{agent_id}/learning
POST /robot/learning/digest
GET  /robot/learning/summary
```

## 운영 대시보드

```http
GET /dashboard/robot-ai
GET /dashboard/robot-ai/gui
GET /dashboard/robot-autonomy-baseline
POST /dashboard/robot-autonomy-baseline
POST /dashboard/robot-autonomy-baseline/reload
```

## DB Bridge

```http
GET  /db-bridge/states
GET  /db-bridge/events
GET  /db-bridge/feedback
POST /db-bridge/decision
POST /db-bridge/trace
```

## 기타 운영

```http
POST /alerts/evaluate
POST /dashboard/shards-weighted
POST /dashboard/rebalance
POST /ops/scheduler/run
```
