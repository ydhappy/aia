# AIA - Lightweight Game AI Bridge Server

경량 LLM/AI 에이전트 서버 예제입니다. 기존 **Java 8 게임 서버**와 안전하게 연동하는 것을 목표로 하며, 게임 서버는 상태를 전달하고 AI 서버는 **허용된 액션 하나만 추천**합니다.

## 목표
- 기존 Java 8 서버 유지
- AI 서버는 별도 프로세스로 분리
- 경량/저지연 우선
- 규칙 엔진 우선, LLM은 보조 판단만 수행
- 장애 시 즉시 폴백

## 핵심 구조
- **Java 8 Game Server**: 상태 수집, 실제 액션 실행, 검증
- **FastAPI AI Bridge**: `/observe`, `/decide`, `/health`, `/metrics`
- **Policy Engine**: 규칙 엔진 + 상태 기반 의사결정
- **LLM Client**: llama.cpp 또는 Ollama 연동
- **State Store**: 최근 상태, 마지막 행동, 실패 횟수 저장

## 실행 API
### `POST /observe`
상태 적재 전용입니다.

### `POST /decide`
현재 상태를 기반으로 허용 액션 하나를 반환합니다.

### `GET /health`
앱/LLM/캐시 상태를 반환합니다.

### `GET /metrics`
간단한 운영 지표를 반환합니다.

## 허용 액션
- `MOVE`
- `ATTACK`
- `USE_SKILL`
- `RETREAT`
- `PICKUP`
- `IDLE`

## 요청 예시
```json
{
  "agent_id": "bot_001",
  "tick": 101,
  "state": {
    "hp": 45,
    "mp": 20,
    "x": 100,
    "y": 200,
    "target_id": "mob_1",
    "target_distance": 1,
    "is_under_attack": true,
    "cooldowns": {
      "heal": 0,
      "fireball": 5
    },
    "inventory": {
      "potion": 2
    }
  }
}
```

## 응답 예시
```json
{
  "action": "USE_SKILL",
  "action_args": {
    "skill": "heal",
    "target": "self"
  },
  "confidence": 0.98,
  "reason": "low_hp_and_heal_ready",
  "source": "rule_engine"
}
```

## Java 8 연동 방식
AI 서버는 HTTP REST 기준입니다. Java 8 서버에서 상태를 JSON으로 보내고, AI 응답을 파싱한 후 **서버 측 검증**을 거쳐 실제 행동을 실행합니다.

### Java 8 권장 연동 순서
1. 게임 상태 수집
2. `/observe` 호출
3. 행동 필요 시 `/decide` 호출
4. 반환 액션 검증
5. 실제 게임 서버에서 실행

### Java 8 예시 흐름
- 저HP + heal 쿨다운 0 → `USE_SKILL(heal)`
- 근접 타겟 존재 → `ATTACK`
- 타겟 없음 → `IDLE`
- 위험 상태 → `RETREAT`

## 로컬 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker 실행
```bash
docker compose up --build
```

## 환경변수
`.env.example` 참고

## LLM 백엔드
운영:
- `llama.cpp server` 권장

개발:
- `Ollama` 지원

기본 동작은 **규칙 엔진 우선**입니다. LLM은 필요한 경우에만 사용합니다.

## 안정화 원칙
- 매 틱 LLM 호출 금지
- 액션 화이트리스트 강제
- 잘못된 LLM 응답 즉시 폴백
- 타임아웃 필수
- 게임 액션은 AI 서버가 직접 실행하지 않음
- 실제 액션 실행은 Java 8 서버가 담당

## 토크 / 멘트
- 가볍고 안정적으로 게임 서버와 연동되는 AI 브리지 서버를 목표로 합니다.
- 모든 판단을 LLM에 맡기지 않고, 규칙 엔진과 상태머신을 중심으로 운영 안정성을 확보합니다.
- 코드량보다 단순성, 추적 가능한 로그, 실패 시 폴백을 우선합니다.

## 다음 확장 포인트
- Redis 연동 고도화
- llama.cpp JSON 응답 강제 프롬프트 개선
- Java 8 샘플 클라이언트 추가
- GitHub Actions 확장
- NPC 대화용 보조 LLM 노드 추가
