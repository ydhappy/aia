# AIA

AIA는 기존 Java 게임서버 옆에 붙이는 **로봇 AI 브리지**입니다.

AIA가 게임서버의 원본 캐릭터/로봇 테이블을 직접 조작하지 않습니다. AIA는 로봇 생성 요청, 판단 API, 학습, 대시보드를 제공하고, 실제 로봇 생성과 월드 등록은 기존 게임서버가 직접 수행합니다.

## 핵심 개념

```text
AIA
  -> 로봇 생성 요청을 MySQL queue에 저장
  -> 로봇 profile/판단/학습/API/dashboard 제공

기존 게임서버
  -> queue에서 pending 요청 poll
  -> 서버 IdFactory로 objectId 발급
  -> 서버 DB insert
  -> inventory/skill 지급
  -> World spawn
  -> AI scheduler 등록
  -> tick마다 AIA ops-tick 호출
```

## 왜 이 구조인가

기존 게임서버마다 objectId, character table, robot table, inventory, skill, world spawn, AI scheduler 구현이 다릅니다. 그래서 AIA가 서버 DB에 직접 insert하지 않고, `AiaRobotSpawnAdapter`를 통해 기존 서버 코드가 직접 생성하게 합니다.

이 방식의 장점:

```text
서버 원본 구조 보존
중복 objectId 방지
서버별 DB schema 차이 흡수
월드 객체/AI scheduler 정상 등록
AIA 장애 시에도 게임서버 보호
```

## 빠른 시작

### 1. 설치

```bash
git clone <repo-url>
cd aia
python -m venv .venv
python -m pip install -r requirements.txt
```

또는:

```bash
python runners/setup/bootstrap_local.py
```

### 2. `.env` 설정

```env
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8000
ENABLE_API_KEY_AUTH=false
DB_BRIDGE_BACKEND=mysql
DB_BRIDGE_MYSQL_DSN=mysql+pymysql://root:password@127.0.0.1:3306/your_game_db
STATE_STORE_MODE=memory
```

외부/LAN에 열 경우:

```env
ENABLE_API_KEY_AUTH=true
API_KEY=충분히_긴_랜덤_키
```

### 3. MySQL 5.5 SQL 적용

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

확인:

```http
GET /health/details
```

정상 기준:

```text
mysql.status = ok
mysql.missing_tables = []
```

### 4. AIA 실행

```bash
python runners/server/run_local_aia.py
```

### 5. 생성 요청 넣기

```http
POST /robot/spawn-requests
```

```json
{
  "server_name": "main",
  "count": 30,
  "classes": ["knight", "elf", "wizard"],
  "level_min": 1,
  "level_max": 30,
  "default_x": 32670,
  "default_y": 32790,
  "default_map": 4
}
```

### 6. Java 외부 설정 파일 준비

기존 게임서버의 설정 폴더에 예시 파일을 복사합니다.

```text
integration/java8/aia-server.properties.example -> config/aia-server.properties
```

수정할 값:

```properties
aia.baseUrl=http://127.0.0.1:8000
aia.apiKey=
aia.jdbcUrl=jdbc:mysql://127.0.0.1:3306/your_game_db?useUnicode=true&characterEncoding=utf8
aia.dbUser=root
aia.dbPassword=password
aia.serverName=main
aia.spawnBatchSize=20
aia.healthCheckBeforeSpawn=true
aia.connectTimeoutMs=3000
aia.readTimeoutMs=5000
```

### 7. 기존 게임서버에 붙일 Java 파일

아래 파일을 기존 게임서버 소스에 복사합니다.

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaServerConfig.java
integration/java8/AiaServerConnector.java
integration/java8/aia-server.properties.example
integration/java8/AiaRobotSpawnRequest.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnPoller.java
integration/java8/AiaDecisionParser.java
integration/java8/DbDecisionPoller.java
```

권장 연결 방식은 `AiaServerConnector.fromFile()`입니다.

```java
private static AiaServerConnector aiaConnector;

private void bootAiaRobots() throws Exception {
    aiaConnector = AiaServerConnector.fromFile(
        "config/aia-server.properties",
        new MyServerAiaRobotAdapter()
    );
    int processed = aiaConnector.bootSpawnOnce();
    System.out.println("[AIA] spawn processed=" + processed);
}
```

넣는 위치:

```text
서버 DB 로드 완료 후
맵/NPC/월드 로드 완료 후
유저 접속 오픈 전 또는 게임 루프 시작 직전
```

자세한 위치와 Adapter 구현 예시는 `docs/USAGE.md`에 있습니다.

## 기존 서버에서 반드시 작성해야 하는 코드

기존 게임서버 프로젝트 안에 서버 전용 Adapter를 만듭니다.

```java
public class MyServerAiaRobotAdapter implements AiaRobotSpawnAdapter {
    public boolean exists(AiaRobotSpawnRequest request) throws Exception {
        return false;
    }

    public long createAndSpawn(AiaRobotSpawnRequest request) throws Exception {
        // 1. 기존 서버 IdFactory로 objectId 발급
        // 2. 기존 서버 robot/character 테이블 insert
        // 3. 기본 아이템/스킬 지급
        // 4. request.locX / locY / locMap / heading 적용
        // 5. 기존 World에 로봇 객체 등록
        // 6. 기존 AI scheduler에 등록
        // 7. objectId 반환
        return 0L;
    }

    public void afterSpawn(AiaRobotSpawnRequest request, long serverObjectId) throws Exception {
        // 로그, 브로드캐스트, 추가 초기화
    }
}
```

서버마다 클래스명이 다르므로 위 코드는 그대로 끝나는 코드가 아니라, 기존 서버의 `IdFactory`, `CharacterTable`, `RobotTable`, `World`, `Inventory`, `Skill`, `AI scheduler`에 연결해야 하는 위치를 보여주는 기준 코드입니다.

## AI tick에서 AIA 호출

서버 로봇 AI loop에서는 connector를 재사용합니다.

```java
String json = buildOpsTickJson(robot);
String response = aiaConnector.opsTick(json);
// AiaDecisionParser로 파싱 후 서버 move/attack/skill 함수 실행
```

## 운영 확인

Spawn Queue:

```http
GET /dashboard/robot-spawn-queue/gui?server_name=main
GET /dashboard/robot-spawn-queue/gui?status=failed&server_name=main
```

복구:

```http
POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

AI 대시보드:

```http
GET /dashboard/robot-ai/gui
```

## 현재 짧은 파일 구조

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

## 테스트

전체 점검:

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

MySQL 통합 테스트:

```bash
AIA_TEST_MYSQL_DSN=mysql+pymysql://root:root@127.0.0.1:3306/aia_ci \
python -m pytest tests/test_mysql_spawn_queue_integration.py
```

## 상세 문서

```text
docs/USAGE.md                 실제 서버 연동 절차
docs/SERVER-INTEGRATION.md    서버 연동 상세
docs/API.md                   API 요약
docs/PROJECT-STRUCTURE.md     폴더 구조
docs/REFACTOR-CHECKLIST.md    정리 내역
docs/THIRD-PARTY-REVIEW.md    제3자 점검
```
