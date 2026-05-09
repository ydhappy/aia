# AIA 빠른 시작

AIA는 게임서버 옆에서 실행되는 Python 기반 로봇 AI 브리지입니다. 게임서버는 실제 로봇 생성, 이동, 공격, 스킬, 월드 등록을 담당하고 AIA는 판단, 프로필, 학습, 대시보드, 생성 요청 큐를 담당합니다.

## 1. 실행

```bash
python one_click_start.py
```

기본 주소는 다음입니다.

```text
http://127.0.0.1:8000
```

수동 실행이 필요하면 다음 순서로 진행합니다.

```bash
python scripts/bootstrap_local.py
python scripts/run_local_aia.py
```

## 2. 기본 확인

```http
GET /health
GET /metrics
GET /dashboard/robot-ai/gui
```

## 3. 로봇 없는 서버에 붙이는 순서

1. 게임 DB에 `sql/aia_robot_spawn_request_mysql55.sql` 적용.
2. AIA에서 `POST /robot/spawn-requests`로 로봇 생성 요청 생성.
3. 게임서버 시작 루틴에서 `AiaRobotSpawnPoller.runOnce()` 호출.
4. 서버별 `AiaRobotSpawnAdapter.createAndSpawn()`에 기존 서버의 `IdFactory`, DB insert, inventory/skill 지급, world spawn 로직 연결.
5. 생성된 로봇은 AIA `/robot/profile`에 자동 등록됩니다.

## 4. 최소 품질 확인

```bash
pytest tests/test_robot_crud_api.py
pytest tests/test_robot_spawn_request_api.py
pytest tests/test_spawn_request_dashboard.py
```

Windows 전체 게이트:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_quality_gates.ps1
```

## 5. 핵심 화면

```http
GET /dashboard/robot-ai/gui
GET /dashboard/robot-spawn-queue/gui
GET /dashboard/robot-spawn-queue/gui?status=failed
```
