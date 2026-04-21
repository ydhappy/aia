# AIA 구성 및 구현 제안

## 1. 목표
AIA는 다양한 게임 서버와 연동되는 경량 로봇 AI 브리지 서버입니다. 목표는 다음과 같습니다.

- 게임 서버는 최대한 가볍게 유지
- 로봇/NPC 관련 상태, 이벤트, 프로필을 중앙에서 흡수
- 규칙 엔진 우선, LLM은 보조 판단으로 제한
- 자체 LLM 서버와 연동 가능
- Redis 기반 공유 상태 저장 지원
- 다중 서버 / 다중 월드 / 다중 로봇 운영 지원

---

## 2. 권장 구성안

### 권장 기본형
- Game Server (Java/C++/C#/Go/Node/Python)
- AIA Bridge Server (FastAPI)
- Self-Hosted LLM Server (OpenAI-compatible or llama.cpp style)
- Redis

### 권장 데이터 흐름
1. 게임 서버가 로봇 상태를 수집
2. AIA `/robot/profile` 로 기본 프로필 저장
3. AIA `/robot/event` 로 중요한 이벤트 저장
4. AIA `/observe` 또는 `/observe/batch` 로 상태 적재
5. AIA `/decide` 또는 `/decide/batch` 로 다음 행동 조회
6. 게임 서버가 액션 검증 후 실제 실행
7. 필요 시 `/robot/{agent_id}/trace` 로 판단 흐름 점검

---

## 3. 모듈별 책임

### Game Server
- 실제 게임 로직 수행
- 좌표/스킬/타겟/맵 검증
- 최종 액션 실행 권한 보유

### AIA
- 로봇 상태/이벤트/프로필 흡수
- 위험도 계산
- 역할/성향별 전략 선정
- 규칙 엔진 판단
- 필요 시 자체 LLM 서버에 질의
- 안전 파싱 및 최종 액션 검증

### Self-Hosted LLM Server
- 자연어 기반 보조 판단
- 고수준 상황 요약
- 복잡한 예외 상황에서 JSON 액션 추천

### Redis
- 최근 상태 저장
- 프로필 저장
- 이벤트 저장
- trace 저장
- 다중 AIA 인스턴스 간 공유 상태

---

## 4. 구현 우선순위 제안

### 1단계: 현재 구조 유지 + 운영 적용
- memory/redis store 선택 가능 유지
- self-hosted LLM 연동 유지
- batch 및 websocket 사용처 분리
- Java/C++ 서버 연동 시작

### 2단계: 운영 안정화
- request_id 기반 구조화 로그 강화
- API key 기본 활성화 옵션화
- Redis 연결 실패 폴백 처리
- LLM timeout / circuit breaker 추가

### 3단계: 정책 분리
- healer / tank / dealer / collector / support 정책 파일 분리
- 월드/맵/사냥터별 정책 override 지원
- bot group template 도입

### 4단계: 추론 최적화
- llm_hint 발생 조건 최적화
- trace 샘플 분석
- 불필요한 LLM 호출 제거
- prompt compression / context slimming 적용

### 5단계: 운영 도구
- 관리자용 trace viewer
- batch 상태 점검 API
- bot health dashboard
- 정책 hot-reload

---

## 5. 권장 배포 형태

### 소규모
- game server 1대
- aia 1대
- self-hosted llm 1대
- redis 1대

### 중규모
- world server 여러 대
- aia 2대 이상
- shared redis
- self-hosted llm 1대 또는 2대

### 대규모
- world/shard별 aia 분리
- llm inference pool 분리
- redis HA 구성
- batch 전용 gateway 추가

---

## 6. 서버 연동 방식 제안

### Java 8 / Java 17
- HTTP REST 기본
- 대량 봇은 batch API 사용
- trace 조회는 운영 도구만 사용

### C++
- libcurl + JSON 라이브러리
- 월드 서버 또는 AI proxy 프로세스에서 AIA 호출

### C#
- 관리 서버 또는 bot manager에서 HttpClient 사용

### Go / Node.js / Python
- gateway / orchestration / tooling 역할에 적합

---

## 7. 운영 원칙
- LLM은 항상 보조 판단
- 게임 서버는 최종 실행자
- 액션 화이트리스트 강제
- trace는 진단용
- 고주기 틱마다 LLM 호출 금지
- 이벤트는 의미 있는 것만 적재

---

## 8. 권장 추가 작업

### 바로 할 것
- `.env.example` 최종 정리
- Redis 연결 예외 처리 강화
- 정책 파일 분리 시작
- Java/C++/Go batch 예제 추가

### 다음 단계
- role-based policy package 구성
- websocket 인증 보강
- world-specific config 지원
- 운영용 dashboard 초안

---

## 9. 최종 제안
가장 좋은 운영 형태는 다음과 같습니다.

- 게임 서버는 게임 로직과 검증만 담당
- AIA는 상태 흡수, 정책 판단, trace 저장 담당
- 자체 LLM 서버는 별도 추론 노드로 분리
- Redis는 공용 기억 저장소로 사용

이 구조가 가장 가볍고, 유지보수 가능하며, 확장에 유리합니다.
