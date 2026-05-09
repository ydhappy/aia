# AIA

AIA는 게임서버 옆에서 실행되는 **Python 기반 로봇 AI 브리지**입니다.
게임서버는 실제 로봇 객체 생성, 이동, 공격, 스킬, 월드 등록을 담당하고 AIA는 판단, 프로필, 학습, 생성 요청 큐, 대시보드를 담당합니다.

원클릭 실행 방식은 제거했습니다. 서버 연동 기준으로 직접 설치, DB 적용, AIA 실행, 게임서버 poller 연결 순서로 사용합니다.

## 폴더 구조

```text
app/                 순수 Python 애플리케이션 코드
sql/                 MySQL 5.5 호환 SQL
integration/java8/   게임서버에 붙일 Java 8 계약/클라이언트 코드
examples/java8/      Java 8 main 예제
runners/             사람이 직접 실행하는 실행 코드
tests/               pytest 테스트
```

상세 구조:

```text
docs/PROJECT-STRUCTURE.md
```

## 기본 사용 순서

1. Python 가상환경 생성 및 의존성 설치.
2. `.env` 설정.
3. MySQL 5.5용 SQL 적용.
4. AIA 실행.
5. `POST /robot/spawn-requests`로 로봇 생성 요청 생성.
6. 게임서버 Java 8 `AiaRobotSpawnPoller`와 `AiaRobotSpawnAdapter` 연결.
7. `/api/v1/robot/ops-tick`으로 판단 루프 연동.
8. `/dashboard/robot-spawn-queue/gui`와 `/dashboard/robot-ai/gui`로 운영 확인.

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

## 로봇 없는 서버 연동 요약

1. 게임 DB에 MySQL 5.5용 큐 테이블 적용.

```bash
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

2. AIA에서 로봇 생성 요청 생성.

```http
POST /robot/spawn-requests
```

3. 게임서버 Java 8 시작 루틴에 poller 연결.

```text
integration/java8/AiaRobotSpawnPoller.java
integration/java8/AiaRobotSpawnAdapter.java
```

4. 서버별 `createAndSpawn()`에 기존 서버의 `IdFactory`, DB insert, world spawn 로직을 연결합니다.

상세 문서:

```text
docs/SERVER-INTEGRATION.md
```

## 주요 API

```http
GET  /health
GET  /metrics
POST /api/v1/robot/ops-tick
GET  /robot
POST /robot/spawn-requests
POST /robot/profile
GET  /dashboard/robot-ai/gui
GET  /dashboard/robot-spawn-queue/gui
POST /dashboard/robot-spawn-queue/retry-failed
POST /dashboard/robot-spawn-queue/recover-claimed
```

전체 API 요약:

```text
docs/API.md
```

## 테스트

개별 테스트:

```bash
pytest tests/test_robot_crud_api.py
pytest tests/test_robot_spawn_request_api.py
pytest tests/test_spawn_request_dashboard.py
pytest tests/test_mysql55_schema_compat.py
```

Linux/GitHub Actions용 전체 게이트:

```bash
python runners/quality/run_quality_gates.py
```

Windows 전체 게이트:

```powershell
powershell -ExecutionPolicy Bypass -File runners/quality/run_quality_gates.ps1
```

GitHub Actions:

```text
.github/workflows/aia-ci.yml
```

push, pull request, 수동 실행 시 Python 테스트와 Java 8 컴파일을 실행합니다.

## 유지 문서

```text
README.md
docs/USAGE.md
docs/SERVER-INTEGRATION.md
docs/API.md
docs/PROJECT-STRUCTURE.md
docs/REFACTOR-CHECKLIST.md
```
