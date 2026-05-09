# AIA 서버 연동 및 사용방법

이 문서는 게임서버에 AIA를 붙여 로봇 자동생성, 판단, 대시보드를 사용하는 실제 절차만 정리합니다.
원클릭 실행 방식은 사용하지 않습니다.

## 1. AIA 역할

AIA는 게임서버를 대신해서 실제 캐릭터를 생성하지 않습니다. AIA는 생성 요청과 AI 판단을 제공하고, 게임서버가 실제 DB insert, objectId 발급, world spawn, 이동/공격/스킬 실행을 담당합니다.

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

## 2. 설치

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

## 3. 환경 설정

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

MySQL 5.5 호환 기준은 `utf8`입니다. `utf8mb4` 전용 설정을 사용하지 않습니다.

## 4. DB 적용

### 4-1. AIA 기본 DB bridge 테이블

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
```

### 4-2. 로봇 자동생성 요청 큐

```bash
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

`aia_robot_spawn_request`는 AIA가 로봇 생성 요청만 넣는 안전 큐입니다. 서버 원본 `robot`, `characters`, `robot_setting` 테이블은 AIA가 직접 수정하지 않습니다.

## 5. AIA 실행

Windows:

```powershell
.\.venv\Scripts\python.exe scripts/run_local_aia.py
```

Linux:

```bash
./.venv/bin/python scripts/run_local_aia.py
```

실행 후 확인:

```http
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/metrics
```

## 6. 로봇 생성 요청 만들기

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

## 7. 게임서버 Java 8 연결

서버에 포함할 주요 파일:

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaRobotSpawnRequest.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnPoller.java
```

게임서버 시작 루틴 예시:

```java
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
```

서버별로 반드시 구현할 부분:

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
        // 4. 좌표, 맵, heading 설정
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

## 8. Spawn Queue 상태 확인

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

## 9. 로봇 판단 루프

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

## 10. 로봇 CRUD

```http
GET    /robot
POST   /robot/profile
PUT    /robot/{agent_id}/profile
PATCH  /robot/{agent_id}/profile
GET    /robot/{agent_id}
DELETE /robot/{agent_id}
```

`DELETE /robot/{agent_id}`는 AIA 내부 runtime/profile/event/trace/learning만 삭제합니다. 게임서버의 실제 DB row와 world 객체는 게임서버가 직접 정리해야 합니다.

## 11. 운영 화면

```http
GET /dashboard/robot-ai/gui
GET /dashboard/robot-spawn-queue/gui
```

## 12. 테스트

```bash
pytest tests/test_robot_crud_api.py
pytest tests/test_robot_spawn_request_api.py
pytest tests/test_spawn_request_dashboard.py
```

Windows 전체 점검:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_quality_gates.ps1
```
