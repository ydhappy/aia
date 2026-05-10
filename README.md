# AIA

AIA는 기존 Java 게임서버 옆에 붙이는 **로봇 AI 브리지**입니다.

AIA가 게임서버의 원본 캐릭터/로봇 테이블을 직접 조작하지 않습니다. AIA는 로봇 생성 요청, 판단 API, 학습, 대시보드를 제공하고, 실제 로봇 생성과 월드 등록은 기존 게임서버가 직접 수행합니다.

서버에 로봇 관련 코드/테이블이 전혀 없는 경우를 위해 최소 로봇 테이블과 JDBC 저장소도 제공합니다.

## 핵심 개념

```text
AIA
  -> 로봇 생성 요청을 queue에 저장
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

## 서버에 로봇이 전혀 없는 경우

최소 로봇 테이블을 먼저 적용합니다.

```bash
mysql -u root -p your_game_db < sql/robot_min_mysql55.sql
```

생성되는 테이블:

```text
robot
robot_item
robot_skill
robot_ai
robot_log
```

이 테이블은 AIA 전용 테이블이 아니라 **기존 게임서버가 소유하는 최소 로봇 테이블**입니다. AIA는 여기에 직접 insert하지 않고, Java `BasicRobotAdapter` 또는 서버 전용 Adapter가 `createAndSpawn()`에서 insert합니다.

## 왜 이 구조인가

기존 게임서버마다 objectId, character table, robot table, inventory, skill, world spawn, AI scheduler 구현이 다릅니다. 그래서 AIA가 서버 DB에 직접 insert하지 않고, `AiaRobotSpawnAdapter`, `AiaRobotActionAdapter`, `AiaSpawnQueue`를 통해 기존 서버 코드가 직접 생성/실행/큐처리를 하게 합니다.

이 방식의 장점:

```text
서버 원본 구조 보존
중복 objectId 방지
서버별 DB schema 차이 흡수
월드 객체/AI scheduler 정상 등록
AIA 장애 시에도 게임서버 보호
MySQL 외 DB는 AiaSpawnQueue 구현으로 확장 가능
로봇 테이블이 없는 서버도 최소 테이블로 시작 가능
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

기본 제공 SQL은 MySQL 5.5 기준입니다.

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

서버에 로봇 테이블이 없다면 추가 적용합니다.

```bash
mysql -u root -p your_game_db < sql/robot_min_mysql55.sql
```

MSSQL/PostgreSQL/SQLite를 queue DB로 쓰려면 `aia_robot_spawn_request`와 AIA bridge 테이블 DDL을 해당 DB 문법에 맞게 만들어야 합니다. Java 쪽 queue 처리는 `AiaSpawnQueue`/`JdbcAiaSpawnQueue`로 분리되어 있습니다.

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
integration/java8/aia-robot-template.properties.example -> config/aia-robot-template.properties
```

`aia-server.properties`는 AIA URL, API key, queue DB, dialect, serverName, timeout을 담당합니다.

```properties
aia.baseUrl=http://127.0.0.1:8000
aia.apiKey=
aia.jdbcUrl=jdbc:mysql://127.0.0.1:3306/your_game_db?useUnicode=true&characterEncoding=utf8
aia.dbUser=root
aia.dbPassword=password
aia.dbDialect=auto
aia.serverName=main
aia.spawnBatchSize=20
aia.healthCheckBeforeSpawn=true
aia.connectTimeoutMs=3000
aia.readTimeoutMs=5000
```

`aia.dbDialect` 값:

```text
auto
mysql
mariadb
postgresql
mssql
sqlite
```

`aia-robot-template.properties`는 서버별 classId, 기본 아이템, 기본 스킬, HP/MP 기본값을 담당합니다.

```properties
aia.class.knight=1
aia.class.elf=2
aia.class.wizard=3
aia.item.knight=1,23,40010,40011
aia.skill.wizard=6,7,8
```

### 7. 기존 게임서버에 붙일 Java 파일

아래 파일을 기존 게임서버 소스에 복사합니다.

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaServerConfig.java
integration/java8/AiaServerConnector.java
integration/java8/AiaRobotTemplateConfig.java
integration/java8/aia-server.properties.example
integration/java8/aia-robot-template.properties.example
integration/java8/AiaSpawnQueue.java
integration/java8/JdbcAiaSpawnQueue.java
integration/java8/AiaSpawnQueueSql.java
integration/java8/AiaRobotSpawnRequest.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnPoller.java
integration/java8/AiaDecision.java
integration/java8/AiaDecisionParser.java
integration/java8/AiaRobotActionAdapter.java
integration/java8/AiaRobotActionRunner.java
integration/java8/RobotStore.java
integration/java8/BasicRobotAdapter.java
integration/java8/DbDecisionPoller.java
```

권장 연결 방식은 `AiaServerConnector.fromFile()`입니다.

```java
private static AiaServerConnector aiaConnector;
private static AiaRobotActionRunner actionRunner;

private void bootAiaRobots() throws Exception {
    AiaRobotTemplateConfig template = AiaRobotTemplateConfig.fromFile("config/aia-robot-template.properties");
    RobotStore store = new RobotStore(
        "jdbc:mysql://127.0.0.1:3306/your_game_db?useUnicode=true&characterEncoding=utf8",
        "root",
        "password"
    );

    BasicRobotAdapter adapter = new BasicRobotAdapter(
        store,
        template,
        new BasicRobotAdapter.ObjectIdProvider() {
            public long nextObjectId() throws Exception {
                return IdFactory.getInstance().nextId();
            }
        }
    );

    aiaConnector = AiaServerConnector.fromFile("config/aia-server.properties", adapter);
    int processed = aiaConnector.bootSpawnOnce();
    actionRunner = new AiaRobotActionRunner(aiaConnector, new MyServerAiaRobotActionAdapter());
    System.out.println("[AIA] spawn processed=" + processed);
}
```

MySQL/MariaDB/PostgreSQL/MSSQL/SQLite 외 구조라면 `AiaSpawnQueue`를 직접 구현해서 아래처럼 주입할 수 있습니다.

```java
AiaSpawnQueue queue = new MyCustomSpawnQueue();
int processed = aiaConnector.bootSpawnOnce(queue);
```

넣는 위치:

```text
서버 DB 로드 완료 후
맵/NPC/월드 로드 완료 후
유저 접속 오픈 전 또는 게임 루프 시작 직전
```

자세한 위치와 Adapter 구현 예시는 `docs/USAGE.md`에 있습니다.

## 기존 서버에서 반드시 작성해야 하는 코드

### Spawn Adapter

서버에 로봇 구조가 이미 있으면 직접 구현합니다.

```java
public class MyServerAiaRobotAdapter implements AiaRobotSpawnAdapter {
    public boolean exists(AiaRobotSpawnRequest request) throws Exception {
        return false;
    }

    public long createAndSpawn(AiaRobotSpawnRequest request) throws Exception {
        // 1. 기존 서버 IdFactory로 objectId 발급
        // 2. 기존 서버 robot/character 테이블 insert
        // 3. config/aia-robot-template.properties 기반 아이템/스킬 지급
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

서버에 로봇 구조가 전혀 없으면 `BasicRobotAdapter`로 시작하고, `afterCreateRows()`를 override해서 실제 World 등록만 붙입니다.

### Action Adapter

```java
public class MyServerAiaRobotActionAdapter implements AiaRobotActionAdapter {
    public String buildOpsTickJson(Object robot) throws Exception { return "{}"; }
    public boolean canExecute(Object robot, AiaDecision decision) throws Exception { return true; }
    public void move(Object robot, AiaDecision decision) throws Exception {}
    public void attack(Object robot, AiaDecision decision) throws Exception {}
    public void useSkill(Object robot, AiaDecision decision) throws Exception {}
    public void retreat(Object robot, AiaDecision decision) throws Exception {}
    public void pickup(Object robot, AiaDecision decision) throws Exception {}
    public void idle(Object robot) throws Exception {}
    public void onError(Object robot, Exception error) throws Exception { idle(robot); }
}
```

서버마다 클래스명이 다르므로 위 코드는 그대로 끝나는 코드가 아니라, 기존 서버의 `IdFactory`, `World`, `Inventory`, `Skill`, `AI scheduler`, `move/attack/skill` 함수에 연결해야 하는 기준 코드입니다.

## AI tick에서 AIA 호출

서버 로봇 AI loop에서는 action runner를 재사용합니다.

```java
actionRunner.tick(robot);
```

`AiaRobotActionRunner`가 내부에서 다음 순서로 처리합니다.

```text
buildOpsTickJson(robot)
-> connector.opsTick(json)
-> AiaDecisionParser.parseOpsTick(response)
-> canExecute(robot, decision)
-> move/attack/useSkill/retreat/pickup/idle 라우팅
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
