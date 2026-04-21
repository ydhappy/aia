# Learning Journal Policy

## 결론
학습/성장 품질을 높이기 위해 기록 저장은 필요합니다.
다만 영구 저장이 아니라, AIA 내부 전용 폴더에 임시로 저장하고 반영 완료 후 정리하는 방식이 적합합니다.

## 목적
- 피드백 직후 학습 상태를 잠깐 보존
- 성장 보정이 적용되기 전 중간 상태를 추적
- 장애나 재시작 시 최근 학습 흔적 확인

## 저장 위치
- `runtime/learning_journal`
- agent_id별 하위 폴더 구조

## 저장 시점
- feedback 처리 시

## 삭제 시점
- autonomous growth rebalance가 적용된 후

## 장점
- 학습/성장 반영 전후를 분리 가능
- 무한 누적을 막음
- 운영 중 필요한 최소 흔적만 유지

## 설정
- `LEARNING_JOURNAL_ENABLED`
- `LEARNING_JOURNAL_PATH`
- `LEARNING_JOURNAL_KEEP_LAST`
