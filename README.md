# AIA

AIA는 게임서버 옆에서 실행되는 **Python 기반 로봇 AI 브리지**입니다.
게임서버는 실제 로봇 객체 생성, 이동, 공격, 스킬, 월드 등록을 담당하고 AIA는 판단, 프로필, 학습, 생성 요청 큐, 대시보드를 담당합니다.

## 빠른 시작

```bash
python one_click_start.py
```

기본 주소:

```text
http://127.0.0.1:8000
```

상세 시작 문서:

```text
docs/QUICKSTART.md
```

## 핵심 구조

```text
Game Server
  - objectId 발급
  - robot/character DB insert
  - world spawn
  - 이동/공격/스킬 실행
  - 최종 검증

AIA
  - 로봇 생성 요청 큐
  - /robot profile 관리
  - observe/decide/ops-tick 판단
  - feedback/learning
  - dashboard/gui
```

## 로봇 없는 서버 연동

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
```

전체 API 요약:

```text
docs/API.md
```

## 테스트

```bash
pytest tests/test_robot_crud_api.py
pytest tests/test_robot_spawn_request_api.py
pytest tests/test_spawn_request_dashboard.py
```

Windows 전체 게이트:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_quality_gates.ps1
```

## 유지 문서

```text
README.md
docs/QUICKSTART.md
docs/SERVER-INTEGRATION.md
docs/API.md
```
