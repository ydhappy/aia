# Runtime Integration Checklist

## 게임 서버 측
- observe 호출 경로 준비
- decide 호출 경로 준비
- profile/event 적재 시점 정의
- action whitelist 검증 구현
- invalid action fallback 구현
- timeout fallback 구현

## AIA 측
- API key 정책 확인
- state store mode 확인
- batch 사용 여부 결정
- websocket 사용 여부 결정
- trace 접근 정책 결정

## Self-Hosted LLM 측
- 추론 서버 주소 확인
- model 이름 확인
- timeout 확인
- JSON 응답 형식 확인
- 내부망 연결 확인

## Redis 측
- 연결 테스트
- key prefix 정책 확인
- persistence 정책 확인
- restart 정책 확인

## 운영 점검
- HP 임계치 확인
- role별 정책 검토
- 이벤트 적재 기준 검토
- LLM 호출 빈도 검토
- 장애 시 fallback 동작 확인
