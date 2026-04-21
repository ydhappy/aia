# AIA

AIA는 게임 서버에 붙는 **운영형 로봇 AI 브리지**입니다.
기존 게임 서버를 유지한 채, 별도 프로세스로 분리 실행되는 Python 기반 AIA가 **판단 / 자동화 / 학습 / 성장 / 복구 / 관제**를 담당하도록 설계되어 있습니다.

기본 권장 구조는 다음과 같습니다.
- **Game Server**: 실제 이동/공격/스킬 실행, 최종 검증, 상태/이벤트/피드백 기록
- **AIA**: decide, automation, growth, anomaly detection, recovery, dashboard, scale
- **DB**: 상태/이벤트/피드백/결정/추적 저장
- **선택**: Redis, self-hosted LLM

DLL/EXE 중심 운영은 더 이상 기본 경로가 아니며, 현재 권장 경로는 **Python + Java 8 + script** 기반 로컬 분리 실행입니다.

---

## 0. 원클릭 시작

가장 쉬운 시작 방법은 아래 한 줄입니다.

```bash
python one_click_start.py
```

이 파일이 자동으로 수행하는 일:
- `.venv` 생성
- pip 업그레이드
- `requirements.txt` 설치
- `.env.example`를 `.env`로 복사
- `runtime/` 및 `runtime/learning_journal/` 생성
- 기본 one-click 모드에서는 `sqlite` 기준으로 AIA 실행
- AIA를 `127.0.0.1:8000` 에서 실행
- 초보자용 안전 기본값 적용
  - `STATE_STORE_MODE=memory`
  - `DB_BRIDGE_BACKEND=sqlite`
  - `ENABLE_API_KEY_AUTH=false`

이 모드는 **초기 구동 / 테스트 / 단일 장비 분리 실행**에 가장 적합합니다.
실운영에서 MySQL/PostgreSQL을 쓸 경우 `.env`만 조정하면 됩니다.

---

## 1. 무엇을 해결하나

AIA는 다음 문제를 해결하기 위한 계층입니다.
- 게임 서버 코드를 크게 뜯지 않고 로봇 AI를 고도화
- 로봇 상태/이벤트/피드백을 흡수해 더 일관된 판단 수행
- 단순 규칙을 넘어 학습/성장/실패 패턴 반영
- 운영 중 recovery, alerts, sharding, rebalance까지 지원
- 같은 서버 내 로컬 HTTP 또는 DB bridge로 저지연 연동

---

## 2. 현재 포함 기능

### 판단 / 전술
- `POST /observe`
- `POST /decide`
- `POST /api/v1/robot/sync`
- rule-engine 우선, LLM은 보조
- growth stage / anomaly / meta policy 반영

### 로봇 지식 / 학습 / 성장
- `POST /robot/profile`
- `POST /robot/event`
- `POST /robot/feedback`
- `GET /robot/{agent_id}`
- `GET /robot/{agent_id}/trace`
- `GET /growth/{agent_id}`
- 행동 학습, group learning, map-aware learning
- growth score, role mastery, map mastery
- failure tag 분석
- autonomous runtime rebalance

### 자동화 / 목표 / 경제 / NPC
- `POST /automation/task`
- `GET /automation/{agent_id}/next-step`
- `GET /goal/{agent_id}`
- goal / state machine / economy / npc 통합 next-step planning

### 운영 / 관제
- `GET /health`
- `GET /metrics`
- `/admin/*`
- `/dashboard/*`
- `/alerts/*`
- `/ops/*`
- `/scale/*`
- weighted shard balancing
- rebalance recommendation
- scheduler batch split
- bulk recover limit

### DB bridge
- `/db-bridge/*`
- SQLite / PostgreSQL / MySQL 지원
- poll limit 적용
- decision / trace batch write 지원

### 멘트 / 토크 / persona
- MBTI / 세대 / 말투 / 줄임말 / 밈 계층
- 반말 / 존댓말 / 반존댓말 / 줄임말 / 밈 톤 지원
- `GET /goal/{agent_id}` 응답에 `persona`, `talk` 포함

---

## 3. 권장 운영 구조

### 가장 권장되는 방식
**같은 서버 내 분리 실행 + DB + 로컬 HTTP 혼합형**

- 게임서버: Java 8
- AIA: Python
- 게임서버 → AIA: `127.0.0.1` 로컬 HTTP
- 게임서버 ↔ DB: 상태/이벤트/피드백/결정 기록
- AIA ↔ DB: poll / write / batch write

이 방식의 장점:
- 외부 서버 불필요
- 지연 최소화
- 게임서버 코드 수정 최소화
- AIA가 주도적으로 운영 가능
- 장애 시 fallback 설계가 명확함

---

## 4. 수동 시작 경로

### 요구사항
- Python 3.11+
- Java 8 서버 연동 시 Java 8 환경
- 선택: PostgreSQL / MySQL / Redis

### 1) 저장소 클론
```bash
git clone <repo-url>
cd aia
```

### 2) 로컬 부트스트랩
```bash
python scripts/bootstrap_local.py
```

### 3) 환경값 확인
`.env`를 열어서 최소한 다음 항목을 확인합니다.
- `ENABLE_API_KEY_AUTH`
- `API_KEY`
- `DB_BRIDGE_BACKEND`
- `DB_BRIDGE_POSTGRES_DSN` 또는 `DB_BRIDGE_MYSQL_DSN`
- `STATE_STORE_MODE`
- `REDIS_URL`

### 4) AIA 실행
```bash
.venv/bin/python scripts/run_local_aia.py
```

Windows라면 가상환경 Python 경로만 맞춰서 실행하면 됩니다.

기본 실행 주소:
- `127.0.0.1:8000`

---

## 5. Java 8 서버 연동

현재 저장소에는 Java 8 최소 연동 스캐폴드가 포함되어 있습니다.

### HTTP 연동기
- `integration/java8/LocalAiaClient.java`

용도:
- `/decide`
- `/api/v1/robot/sync`
- `/robot/feedback`
호출

### DB 혼합형 poller
- `integration/java8/DbDecisionPoller.java`

용도:
- `robot_decision` 테이블의 최신 action 읽기

### 권장 방식
- 상태 / 이벤트 / 피드백 / 장기 이력 → DB
- 즉시 판단 / 긴급 전술 판단 → 로컬 HTTP

즉, **DB + HTTP 혼합형**이 기본 권장안입니다.

---

## 6. 스크립트

### 원클릭 시작
- `one_click_start.py`

### 부트스트랩
- `scripts/bootstrap_local.py`

### 로컬 AIA 실행
- `scripts/run_local_aia.py`

### scheduler cycle 실행
- `scripts/run_scheduler_cycle.py`

### unified API 부하 테스트
- `scripts/load_test_unified.py`

### DB schema 안내
- `scripts/init_db_schema.py`

---

## 7. SQL / DB 시작

### SQL 파일
- `sql/aia_robot_schema.sql`

### MySQL/MariaDB 적용 예시
```bash
mysql -u root -p your_database < sql/aia_robot_schema.sql
```

그 다음 `.env` 예:
```env
DB_BRIDGE_BACKEND=mysql
DB_BRIDGE_MYSQL_DSN=mysql+pymysql://user:password@127.0.0.1:3306/your_database
```

원클릭 모드에서는 기본값으로 `sqlite`를 사용하므로, DB를 따로 준비하지 않아도 AIA 기동 자체는 가능합니다.

---

## 8. 주요 API

### 즉시 판단
- `POST /observe`
- `POST /decide`
- `POST /api/v1/robot/sync`

### 로봇 데이터
- `POST /robot/profile`
- `POST /robot/event`
- `POST /robot/feedback`
- `GET /robot/{agent_id}`
- `GET /robot/{agent_id}/trace`

### 성장 / 목표 / 자동화
- `GET /growth/{agent_id}`
- `GET /goal/{agent_id}`
- `POST /automation/task`
- `GET /automation/{agent_id}/next-step`

### 운영
- `GET /health`
- `GET /metrics`
- `POST /alerts/evaluate`
- `POST /dashboard/shards-weighted`
- `POST /dashboard/rebalance`
- `POST /ops/scheduler/run`

### DB bridge
- `GET /db-bridge/states`
- `GET /db-bridge/events`
- `GET /db-bridge/feedback`
- `POST /db-bridge/decision`
- `POST /db-bridge/trace`

---

## 9. 학습 / 성장 / 기록 저장 정책

학습/성장을 위해 **기록 저장은 필요**하지만, 영구 누적은 권장하지 않습니다.

현재 정책:
- feedback 처리 시 AIA 내부 전용 폴더에 임시 기록 저장
- 저장 위치: `runtime/learning_journal/<agent_id>/...json`
- autonomous growth rebalance 적용 후 자동 정리

즉:
- 학습 반영 전 상태는 잠깐 남기고
- 성장 반영이 끝나면 삭제하는 구조입니다.

관련 설정:
- `LEARNING_JOURNAL_ENABLED`
- `LEARNING_JOURNAL_PATH`
- `LEARNING_JOURNAL_KEEP_LAST`

---

## 10. 운영 안정화 원칙

- 게임서버는 실행과 최종 검증 담당
- AIA는 판단/학습/자동화/복구 담당
- bulk scale에서는 LLM 의존도를 낮추고 rule-engine 우선
- `scheduler_cycle_batch_size` 사용
- `db_bridge_poll_limit`, `db_bridge_write_batch_size` 사용
- `trace_compact_mode` 사용 가능
- weighted shard balancing / rebalance 활용
- alerts로 recovery ratio 등 이상 징후 감시
- 게임서버는 반드시 fallback 보유
  - IDLE
  - RETREAT
  - 기본 서버 AI

---

## 11. 말투 / persona 계층

`profile.metadata`에 다음 필드를 둘 수 있습니다.
- `mbti`
- `generation`
- `speech_level`
- `relationship`
- `speech_mode`
- `slang_level`
- `meme_level`

지원되는 표현 계층 예:
- 반말
- 존댓말
- 반존댓말
- 줄임말
- 밈 톤

`GET /goal/{agent_id}` 응답에는 다음이 함께 포함됩니다.
- `persona`
- `talk`

즉, 행동 이유와 멘트를 운영 로그/NPC 대사/디버그 메시지에 그대로 활용할 수 있습니다.

---

## 12. 현재 기본 방향

AIA의 기본 운영 경로는 다음입니다.
- **Python + Java 8 + script**
- 로컬 분리 실행
- DB + 로컬 HTTP 혼합형
- DLL/EXE 중심 운영은 비권장

관련 참고:
- `docs/python-java-script-only.md`
- `docs/learning-journal-policy.md`
- `docs/persona-layers.md`
- `docs/load-and-sharding.md`
- `docs/alerts-and-batching.md`
- `docs/beginner-start-here.md`

---

## 13. 현재 상태 요약

현재 저장소는 다음을 포함합니다.
- 운영형 로봇 AI 백엔드
- DB bridge
- growth / anomaly / meta policy
- fully integrated automation
- alerts / dashboard / ops / scale
- Java 8 최소 연동 스캐폴드
- clone 직후 바로 시작 가능한 bootstrap / one-click 스크립트

즉, 지금은 **게임서버에 붙여 운영할 수 있는 상태**를 기준으로 정리되어 있습니다.
