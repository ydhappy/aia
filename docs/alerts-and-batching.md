# Alerts and DB Batching

## 추가된 운영 기능
- dashboard summary 기반 alert 평가
- recovery ratio 기반 경보
- DB bridge decision/trace batch write

## Alerts API
- `POST /alerts/evaluate`

## DB bridge batching
- `DB_BRIDGE_WRITE_BATCH_SIZE`
- decision/trace 쓰기는 batch 단위로 제한 가능

## 운영 목적
- 대규모 운영에서 상태 이상을 빠르게 감지
- DB 쓰기 부하를 단건보다 배치로 완화

## 권장 정책
- alert는 운영자/관리 계층에서 사용
- batch size는 DB 성능에 맞게 보수적으로 증가
- recovery ratio가 높을 때는 LLM보다 안정성 우선 모드 사용
