# Final Operating Blueprint

## 목표
- 게임 서버 소스 최소화
- DB 중심 상태 교환
- AIA 쪽 최대 운영 기능 집중
- self-hosted LLM 분리
- Redis 공유 상태
- 단일 운영 통신 키 기반 단순화

## 최종 권장 구성
- Game Server
- Game DB
- AIA Bridge
- Redis
- Self-Hosted LLM

## 서버 역할
- 패킷/전투/이동/스킬 실행
- 최종 실행 검증
- DB 기록
- 최소 observe/feedback 훅

## AIA 역할
- decide
- automation
- learning
- group learning
- map learning
- runtime override
- recovery
- dashboard
- ops scheduler
- scale orchestration
- db bridge

## DB 중심 운영
- robot_state
- robot_event
- robot_feedback
- robot_task
- robot_decision
- robot_trace_summary

## 키 운영
- 서버 <-> AIA 운영 통신용 API key 1개
- GitHub/배포용 token 1개 별도

## 권장 원칙
- 게임 서버 안에 AI 비즈니스 로직 최소화
- AIA가 운영 두뇌 역할
- self-hosted LLM은 보조 판단만 사용
- 대규모 운영은 scale/dashboard/ops API 사용
- 복구는 보수적으로 실행

## 현재 구현 범위 요약
- tactical decision APIs
- unified sync API
- batch / websocket
- autonomous automation tasks
- adaptive learning
- group learning
- map-aware learning
- goal / state machine / economy / npc view
- admin / dashboard / ops / scale / recovery
- db bridge scaffold

## 남은 고도화 포인트
- DB poller/writer 실제 DB 드라이버 연결
- automation next-step에 economy/npc 완전 통합 마무리
- frontend dashboard
- scheduler daemon
- load/performance tuning
