# Load Testing and Sharding

## 포함 기능
- weighted shard balancing
- unified API load test script
- alerts evaluation
- scheduler batch split
- db bridge batch write

## 샤드 운영
- `POST /dashboard/shards`
- `POST /dashboard/shards-weighted`

## 권장 사용
- 단순 균등 분배가 아니라, task/state/learning을 반영한 weighted 분배 권장
- 대규모 운영에서는 shard 단위로 scheduler/recovery 실행

## 부하 테스트
- `scripts/load_test_unified.py`
- unified API 기준 동시 요청 부하를 빠르게 측정 가능

## 운영 목적
- 병목 파악
- DB/Redis/LLM 영향도 분리
- shard 배분 기준 검증
- p50/p95/p99 지연 확인
