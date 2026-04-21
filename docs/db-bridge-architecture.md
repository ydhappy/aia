# DB Bridge Architecture

## 목표
게임 서버는 최소한의 상태/이벤트/피드백만 DB에 기록하고, AIA가 DB를 중심으로 판단과 운영 기능을 수행하는 구조를 정리합니다.

## 권장 테이블 축
- robot_state
- robot_event
- robot_feedback
- robot_task
- robot_decision
- robot_trace_summary

## 최소 컬럼 예시
### robot_state
- agent_id
- tick
- hp
- mp
- x
- y
- map_id
- target_id
- target_distance
- safe_zone
- weight_percent
- updated_at

### robot_event
- agent_id
- tick
- event_type
- severity
- message
- payload_json
- created_at

### robot_feedback
- agent_id
- tick
- action
- reward
- outcome
- map_id
- context_json
- created_at

### robot_task
- task_id
- agent_id
- mode
- status
- priority
- conditions_json
- parameters_json
- updated_at

### robot_decision
- agent_id
- tick
- action
- action_args_json
- confidence
- source
- reason
- created_at

## 운영 흐름
1. 서버가 robot_state / robot_event / robot_feedback 기록
2. AIA가 이를 읽어 판단
3. AIA가 robot_decision / robot_trace_summary 갱신
4. 서버는 robot_decision을 읽거나 API로 받음
5. 서버는 최종 검증 후 실행

## 장점
- 서버 소스 최소화
- 언어와 구조가 다른 서버에도 적용 쉬움
- 장애 분석/재처리/감사 추적 용이
- 대규모 로봇 운영에 유리

## 권장 사항
- 상태 테이블은 upsert 구조 권장
- 이벤트/피드백은 append-only 구조 권장
- 결정 결과는 최근값 + 이력 분리 권장
