# AIA - Lightweight Game AI Bridge Server

경량 LLM/AI 에이전트 서버 예제입니다. 특정 언어에 종속되지 않고 **Java 8 / Java 17 / C++ / C# / Python** 등 다양한 게임 서버와 연동할 수 있도록 설계했습니다. 게임 서버는 상태와 로봇 관련 정보를 전달하고, AI 서버는 **허용된 액션 하나만 추천**합니다.

## 목표
- 기존 게임 서버 유지
- AI 서버는 별도 프로세스로 분리
- 경량/저지연 우선
- 규칙 엔진 우선, LLM은 보조 판단만 수행
- 장애 시 즉시 폴백
- 로봇 관련 정보 흡수 및 재사용
- 경량 AI 에이전트 계층 포함

## 핵심 구조
- **Game Server**: 상태 수집, 실제 액션 실행, 검증
- **FastAPI AI Bridge**: `/observe`, `/decide`, `/health`, `/metrics`
- **Robot Knowledge API**: `/robot/profile`, `/robot/event`, `/robot/{agent_id}`
- **Agent Graph**: 위험도 평가, 전략 선택, LLM 힌트 여부 결정
- **Policy Engine**: 규칙 엔진 + 상태/프로필/이벤트 기반 의사결정
- **LLM Client**: llama.cpp 또는 Ollama 연동
- **LLM Parser**: 안전한 JSON 액션 파싱
- **State Store**: 최근 상태, 프로필, 이벤트, trace 저장

## 실행 API
### `POST /observe`
상태 적재 전용입니다.

### `POST /decide`
현재 상태와 저장된 로봇 지식을 기반으로 허용 액션 하나를 반환합니다.

### `POST /robot/profile`
로봇 프로필을 저장합니다.

### `POST /robot/event`
로봇의 최근 이벤트를 저장합니다.

### `GET /robot/{agent_id}`
해당 로봇의 저장된 프로필, 최근 이벤트, 마지막 상태를 조회합니다.

### `GET /robot/{agent_id}/trace`
해당 로봇의 최신 에이전트 trace를 조회합니다.

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

## 로봇 지식 흡수 범위
- 역할: healer / tank / dealer / collector / support / scout
- 성향: aggressive / defensive / balanced / support
- 선호 스킬 / 금지 스킬
- 파티 정보 / 클랜 정보
- 홈 좌표 / 순찰 포인트
- 태그 / 노트 / 메타데이터
- 최근 이벤트
  - 예: `loot_detected`, `danger_zone`, `boss_spawn`, `party_member_down`
- 전투 상태
  - `nearby_enemies`, `nearby_allies`, `buffs`, `debuffs`, `aggro_targets`

## 요청 예시: 상태
```json
{
  "agent_id": "bot_001",
  "tick": 101,
  "state": {
    "hp": 45,
    "mp": 20,
    "x": 100,
    "y": 200,
    "map_id": 4,
    "heading": 2,
    "target_id": "mob_1",
    "target_distance": 1,
    "target_hp": 80,
    "is_under_attack": true,
    "nearby_enemies": 2,
    "nearby_allies": 1,
    "safe_zone": false,
    "can_teleport": true,
    "weight_percent": 44,
    "cooldowns": {
      "heal": 0,
      "fireball": 5
    },
    "inventory": {
      "potion": 2
    },
    "buffs": [],
    "debuffs": [],
    "aggro_targets": ["mob_1"],
    "extras": {}
  }
}
```

## 요청 예시: 로봇 프로필
```json
{
  "agent_id": "bot_001",
  "name": "PriestAlpha",
  "role": "healer",
  "style": "support",
  "party_id": "party_a",
  "clan_id": "clan_blue",
  "patrol_points": [{"x": 100, "y": 200}, {"x": 110, "y": 205}],
  "preferred_skills": ["support_heal", "heal"],
  "banned_skills": [],
  "tags": ["raid", "night-shift"],
  "notes": ["prioritize party sustain"],
  "metadata": {
    "server_group": "main"
  }
}
```

## 요청 예시: 로봇 이벤트
```json
{
  "agent_id": "bot_001",
  "tick": 102,
  "event_type": "loot_detected",
  "severity": "low",
  "message": "rare item on floor",
  "data": {
    "item_id": "rare_sword"
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

## 연동 방식
AI 서버는 HTTP REST 기준입니다. 어느 언어의 게임 서버든 상태를 JSON으로 보내고, AI 응답을 파싱한 후 **서버 측 검증**을 거쳐 실제 행동을 실행합니다.

### 권장 연동 순서
1. 게임 상태 수집
2. 필요 시 `/robot/profile` 로 로봇 기본 정보 저장
3. 전투/파밍/파티 상황 발생 시 `/robot/event` 로 최근 이벤트 적재
4. `/observe` 호출
5. 행동 필요 시 `/decide` 호출
6. 필요 시 `/robot/{agent_id}/trace` 로 판단 흐름 확인
7. 반환 액션 검증
8. 실제 게임 서버에서 실행

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
- 에이전트 trace는 진단용이며 직접 실행 권한이 없음
- 게임 액션은 AI 서버가 직접 실행하지 않음
- 실제 액션 실행은 게임 서버가 담당

## 토크 / 멘트
- 가볍고 안정적으로 게임 서버와 연동되는 AI 브리지 서버를 목표로 합니다.
- 모든 판단을 LLM에 맡기지 않고, 규칙 엔진과 상태머신을 중심으로 운영 안정성을 확보합니다.
- 로봇의 역할, 성향, 장비 성격, 최근 이벤트를 흡수하여 더 일관된 행동을 유도합니다.
- 에이전트 trace를 제공하여 디버깅과 운영 분석을 쉽게 합니다.
- 코드량보다 단순성, 추적 가능한 로그, 실패 시 폴백을 우선합니다.

## 다음 확장 포인트
- Redis 연동 고도화
- API Key 인증 추가
- Java / C++ / Python 샘플 클라이언트 확장
- GitHub Actions 확장
- NPC 대화용 보조 LLM 노드 추가
- 장기 메모리 / 행동 이력 분석 추가
