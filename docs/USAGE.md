# AIA 서버 연동 및 사용방법

이 문서는 게임서버에 AIA를 붙여 로봇 자동생성, 판단, 대시보드를 사용하는 실제 절차만 정리합니다. 원클릭 실행 방식은 사용하지 않습니다.

## 1. 전체 흐름

```text
1. AIA 설치
2. .env 설정
3. MySQL 5.5 SQL 적용
4. AIA 실행
5. AIA에 로봇 생성 요청 생성
6. 게임서버 시작 루틴에 SpawnPoller 연결
7. 게임서버 Adapter에서 실제 로봇 생성
8. 생성된 로봇을 ops-tick 판단 루프에 연결
9. dashboard/gui로 상태 확인
```

## 2. 역할 분리

AIA는 실제 게임 월드 객체를 만들지 않습니다. AIA는 생성 요청과 AI 판단을 제공하고, 게임서버가 실제 DB insert, objectId 발급, world spawn, 이동/공격/스킬 실행을 담당합니다.

```text
AIA
  - 로봇 생성 요청 생성
  - 로봇 profile 관리
  - observe/decide/ops-tick 판단
  - feedback/learning 저장
  - spawn queue/dashboard 제공

게임서버
  - objectId 발급
  - robot/character DB insert
  - inventory/skill 지급
  - world spawn/despawn
  - 이동/공격/스킬 실행
  - AIA 응답 최종 검증
```

## 3. 설치

```bash
git clone <repo-url>
cd aia
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux:

```bash
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

자동 준비 스크립트:

```bash
python runners/setup/bootstrap_local.py
```

## 4. 환경 설정

`.env.example`을 `.env`로 복사한 뒤 서버 DB에 맞게 수정합니다.

MySQL 5.5 예시:

```env
APP_HOST=127.0.0.1
APP_PORT=8000
ENABLE_API_KEY_AUTH=false
DB_BRIDGE_BACKEND=mysql
DB_BRIDGE_MYSQL_DSN=mysql+pymysql://root:password@127.0.0.1:3306/your_game_db
STATE_STORE_MODE=memory
```

MySQL 5.5 호환 기준은 `utf8`입니다. JDBC도 `characterEncoding=utf8`로 맞춥니다.

## 5. DB 적용

### 5-1. AIA 기본 DB bridge 테이블

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
```

### 5-2. 로봇 자동생성 요청 큐

```bash
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

`aia_robot_spawn_request`는 AIA가 로봇 생성 요청만 넣는 안전 큐입니다. 서버 원본 `robot`, `characters`, `robot_setting` 테이블은 AIA가 직접 수정하지 않습니다.

## 6. AIA 실행

Windows:

```powershell
.\.venv\Scripts\python.exe runners/server/run_local_aia.py
```

Linux:

```bash
./.venv/bin/python runners/server/run_local_aia.py
```

실행 후 확인:

```http
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/metrics
```

## 7. 로봇 생성 요청 만들기

AIA HTTP API로 생성 요청을 넣습니다.

```http
POST /robot/spawn-requests
```

예시:

```json
{
  "server_name": "main",
  "count": 30,
  "classes": ["knight", "elf", "wizard"],
  "level_min": 1,
  "level_max": 30,
  "priority": 100,
  "default_x": 32670,
  "default_y": 32790,
  "default_map": 4,
  "metadata": {
    "memo": "server bootstrap robots"
  }
}
```

결과는 `aia_robot_spawn_request`에 `pending` 상태로 저장됩니다.

## 8. 게임서버에 넣을 Java 파일

서버에 포함할 주요 파일:

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaRobotSpawnRequest.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnPoller.java
```

선택 예제:

```text
examples/java8/RobotCrudExample.java
examples/java8/AiaRobotSpawnExample.java
```

## 9. 게임서버 시작 루틴 연결

게임서버가 DB/NPC/맵/월드 기본 로드를 끝낸 뒤, 게임 루프 시작 전에 poller를 한 번 실행하는 방식이 가장 안전합니다.

```text
Server.start()
  -> loadConfig()
  -> loadDatabase()
  -> loadWorld()
  -> loadNpc()
  -> loadMaps()
  -> runAiaRobotSpawnPoller()
  -> startGameLoop()
```

Java 예시:

```java
private void runAiaRobotSpawnPoller() throws Exception {
    LocalAiaClient aia = new LocalAiaClient("http://127.0.0.1:8000", "");
    AiaRobotSpawnAdapter adapter = new MyServerRobotAdapter();

    AiaRobotSpawnPoller poller = new AiaRobotSpawnPoller(
        "jdbc:mysql://127.0.0.1:3306/your_game_db?useUnicode=true&characterEncoding=utf8",
        "root",
        "password",
        "main",
        aia,
        adapter
    );

    poller.setBatchSize(20);
    poller.runOnce();
}
```

## 10. 서버 Adapter 구현

서버별로 반드시 구현할 부분입니다. 여기에서 실제 서버의 `IdFactory`, `RobotTable`, `World`, `Inventory`, `Skill` 로직을 연결합니다.

```java
public class MyServerRobotAdapter implements AiaRobotSpawnAdapter {
    public boolean exists(AiaRobotSpawnRequest request) throws Exception {
        // agent_id 또는 name 기준으로 이미 생성된 로봇인지 확인
        return false;
    }

    public long createAndSpawn(AiaRobotSpawnRequest request) throws Exception {
        // 1. 서버 IdFactory로 objectId 발급
        // 2. 서버 robot/character 테이블 insert
        // 3. 기본 inventory/skill 지급
        // 4. request.locX, request.locY, request.locMap, request.heading 적용
        // 5. World에 객체 등록
        // 6. AI scheduler에 등록
        // 7. 생성된 objectId 반환
        return 0L;
    }

    public void afterSpawn(AiaRobotSpawnRequest request, long serverObjectId) throws Exception {
        // 로그, 브로드캐스트, 추가 초기화
    }
}
```

## 11. Adapter 구현 체크리스트

```text
objectId가 서버 IdFactory에서 발급되는가?
DB insert와 world spawn이 같은 로봇 정보를 쓰는가?
좌표/map/heading이 request 값과 일치하는가?
inventory/skill 기본값이 비어 있지 않은가?
AI scheduler에 등록되는가?
중복 name/agent_id 생성이 막히는가?
예외 발생 시 failed 상태로 남는가?
```

## 12. Spawn Queue 상태 확인

```http
GET /dashboard/robot-spawn-queue
GET /dashboard/robot-spawn-queue/gui
GET /dashboard/robot-spawn-queue/gui?status=failed
```

상태 의미:

```text
pending : 서버가 아직 처리하지 않음
claimed : 서버가 처리 대상으로 잡음
done    : 생성 완료
failed  : 생성 실패
```

복구 API:

```http
POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

## 13. 로봇 판단 루프

로봇이 생성된 뒤 게임서버는 tick마다 AIA에 상태를 보내고 판단을 받습니다.

권장 API:

```http
POST /api/v1/robot/ops-tick
```

게임서버는 AIA 응답을 바로 실행하지 말고 반드시 검증합니다.

검증 항목:

```text
맵 일치 여부
이동 가능 타일 여부
타겟 생존 여부
거리/쿨타임 조건
안전지대 전투 금지
HP/MP/무게 조건
스킬 사용 가능 여부
```

## 14. 로봇 CRUD

```http
GET    /robot
POST   /robot/profile
PUT    /robot/{agent_id}/profile
PATCH  /robot/{agent_id}/profile
GET    /robot/{agent_id}
DELETE /robot/{agent_id}
```

`DELETE /robot/{agent_id}`는 AIA 내부 runtime/profile/event/trace/learning만 삭제합니다. 게임서버의 실제 DB row와 world 객체는 게임서버가 직접 정리해야 합니다.

## 15. 운영 화면

```http
GET /dashboard/robot-ai/gui
GET /dashboard/robot-spawn-queue/gui
GET /dashboard/robot-spawn-queue/gui?status=failed
```

Spawn Queue GUI는 `total`, `needs_attention`, `pending/claimed/done/failed` 카드, failed 재시도, claimed 복구 버튼을 제공합니다.

## 16. 테스트

```bash
pytest tests/test_robot_crud_api.py
pytest tests/test_robot_spawn_request_api.py
pytest tests/test_spawn_request_dashboard.py
pytest tests/test_mysql55_schema_compat.py
```

Smoke 테스트:

```bash
python runners/smoke/ops_tick_smoke.py
python runners/smoke/robot_crud_smoke.py
```

Windows 전체 점검:

```powershell
powershell -ExecutionPolicy Bypass -File runners/quality/run_quality_gates.ps1
```
