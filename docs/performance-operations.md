# Performance and Operations

## 목표
예시나 샘플이 아니라 실제 운영관리성과 성능을 기준으로 AIA를 운용하기 위한 기준을 정리합니다.

## 핵심 원칙
- 게임 서버는 실행과 검증에 집중
- AIA는 판단/자동화/학습/복구에 집중
- 대규모 운영에서는 LLM 의존도를 낮추고 rule-engine 비중을 높임
- DB bridge는 읽기/쓰기 한도를 명확히 두고 운용
- Redis를 기본 상태 저장소로 사용 권장

## 성능 우선 권장값
- `STATE_STORE_MODE=redis`
- `DB_BRIDGE_BACKEND=postgresql` 또는 `mysql`
- `LLM_DISABLE_FOR_BULK_SCALE=true`
- `TRACE_STORE_ENABLED=true`
- `TRACE_COMPACT_MODE=true` 또는 운영 정책상 요약 저장
- `MAX_BATCH_SIZE`는 서버 성능에 맞게 조정
- `SCHEDULER_CYCLE_BATCH_SIZE`는 100~500 범위에서 시작

## 대규모 운영 기준
### 10 ~ 100
- unified API 또는 direct decide 사용 가능
- Redis 권장

### 100 ~ 1000
- batch 사용 권장
- scale API 사용 권장
- LLM selective mode 권장

### 1000 ~ 10000
- world/shard 분리 필수
- scale batches 사용
- bulk recovery는 묶음 단위 사용
- DB는 PostgreSQL 또는 MySQL 권장
- SQLite는 데모/단일 노드용으로만 제한

## 운영 위험요소
- LLM 과다 사용으로 인한 지연
- trace 과다 저장으로 인한 I/O 증가
- DB bridge polling 과다 주기
- 대량 recover 호출의 순간 부하

## 권장 대응
- rule-engine 우선
- trace compact mode 사용
- scheduler cycle batch 분할
- bulk recover 상한 유지
- shard 단위 격리 운용
