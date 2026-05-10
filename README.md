# AIA

AIA는 게임서버 옆에서 실행되는 **Python 기반 로봇 AI 브리지**입니다.

게임서버는 실제 로봇 객체 생성, DB insert, 월드 등록, 이동, 공격, 스킬 실행을 담당합니다. AIA는 로봇 생성 요청 큐, 판단 API, 프로필, 학습, 대시보드를 담당합니다.

원클릭 실행 방식과 예제/샘플 전용 코드는 제거했습니다. 현재 기준은 **서버 연동용 코드와 운영 문서만 유지**하는 구조입니다.

## 핵심 구조

```text
AIA HTTP API
  -> MySQL 5.5 spawn queue
  -> Java 8 AiaRobotSpawnPoller
  -> 게임서버 AiaRobotSpawnAdapter 구현
  -> 서버 IdFactory / DB insert / World spawn / AI scheduler
```

AIA는 서버 원본 `robot`, `characters`, `robot_setting` 테이블을 직접 수정하지 않습니다.

## 폴더 구조

```text
app/                 Python 애플리케이션 코드
app/core/            설정, 보안, 공통 상수, live JSON loader
app/models/          짧은 모델 파일(req/res/dash/uni/auto/batch)
app/services/        서비스 로직(spawn/spawn_dash/autonomy 등)
app/ui/              HTML UI 렌더러
sql/                 MySQL 5.5 호환 SQL
integration/java8/   게임서버에 붙일 Java 8 계약/클라이언트 코드
runners/             사람이 직접 실행하는 실행 코드
tests/               pytest 테스트
```

상세 구조:

```text
docs/PROJECT-STRUCTURE.md
```

## 공식 짧은 파일명

```text
app/models/req.py       요청 모델
app/models/res.py       응답 모델
app/models/dash.py      Dashboard 모델
app/models/uni.py       통합 API 모델
app/models/auto.py      Automation 모델
app/models/batch.py     Batch 모델

app/services/spawn.py       로봇 생성 요청 서비스
app/services/spawn_dash.py  Spawn Queue 대시보드 서비스
app/services/autonomy.py    자율운영 설정/프로필 서비스
app/ui/spawn_queue.py       Spawn Queue GUI
```

## 기본 사용 순서

1. Python 가상환경 생성 및 의존성 설치.
2. `.env` 설정.
3. MySQL 5.5용 SQL 적용.
4. AIA 실행.
5. `POST /robot/spawn-requests`로 로봇 생성 요청 생성.
6. 게임서버 Java 8 `AiaRobotSpawnPoller`와 `AiaRobotSpawnAdapter` 연결.
7. `/api/v1/robot/ops-tick`으로 판단 루프 연동.
8. `/dashboard/robot-spawn-queue/gui?server_name=main`과 `/dashboard/robot-ai/gui`로 운영 확인.

자세한 사용방법:

```text
docs/USAGE.md
```

## 실행

설치/준비:

```bash
python runners/setup/bootstrap_local.py
```

AIA 실행:

```bash
python runners/server/run_local_aia.py
```

Smoke 테스트:

```bash
python runners/smoke/ops_tick_smoke.py
python runners/smoke/robot_crud_smoke.py
```

## DB 적용

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

적용 후 확인:

```http
GET /health/details
```

`mysql.missing_tables`가 빈 배열이어야 합니다.

## 로봇 없는 서버 연동 요약

1. 게임 DB에 MySQL 5.5용 SQL을 적용합니다.
2. AIA에서 로봇 생성 요청을 생성합니다.
3. 게임서버 Java 8 시작 루틴에 poller를 연결합니다.
4. 서버별 Adapter의 `createAndSpawn()`에 기존 서버의 `IdFactory`, DB insert, world spawn, AI scheduler 로직을 연결합니다.

서버 연동 문서:

```text
docs/SERVER-INTEGRATION.md
```

## 주요 API

```http
GET  /health
GET  /health/details
GET  /metrics
POST /api/v1/robot/ops-tick
GET  /robot
POST /robot/spawn-requests
POST /robot/profile
GET  /dashboard/robot-ai/gui
GET  /dashboard/robot-spawn-queue/gui?server_name=main
POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

전체 API 요약:

```text
docs/API.md
```

## 테스트

권장 전체 점검:

```bash
python runners/quality/run_quality_gates.py
```

주요 개별 테스트:

```bash
pytest tests/test_mods.py
pytest tests/test_auto_live.py
pytest tests/test_spawn_api.py
pytest tests/test_spawn_dash.py
pytest tests/test_spawn_ui.py
pytest tests/test_mysql55.py
```

선택형 MySQL 통합 테스트:

```bash
AIA_TEST_MYSQL_DSN=mysql+pymysql://root:root@127.0.0.1:3306/aia_ci \
python -m pytest tests/test_mysql_spawn_queue_integration.py
```

Windows 전체 게이트:

```powershell
powershell -ExecutionPolicy Bypass -File runners/quality/run_quality_gates.ps1
```

## 유지 문서

```text
README.md
docs/USAGE.md
docs/SERVER-INTEGRATION.md
docs/API.md
docs/PROJECT-STRUCTURE.md
docs/REFACTOR-CHECKLIST.md
docs/THIRD-PARTY-REVIEW.md
```
