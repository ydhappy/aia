# AIA API 요약

## 기본

```http
GET /health
GET /metrics
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

## Spawn Queue 대시보드

```http
GET  /dashboard/robot-spawn-queue
GET  /dashboard/robot-spawn-queue/gui
GET  /dashboard/robot-spawn-queue?status=failed
GET  /dashboard/robot-spawn-queue/gui?status=failed
POST /dashboard/robot-spawn-queue/retry-failed
POST /dashboard/robot-spawn-queue/recover-claimed
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
