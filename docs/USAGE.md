# AIA 서버 연동 상세 사용방법

이 문서는 기존 Java 게임서버에 AIA를 붙이는 실제 작업 순서를 설명합니다. 핵심은 AIA가 서버 DB에 직접 로봇을 insert하지 않고, 기존 게임서버가 `AiaRobotSpawnAdapter`를 구현하여 자기 방식대로 로봇을 생성하게 하는 것입니다.

## 1. 전체 구조

```text
AIA
  - HTTP API 제공
  - 로봇 생성 요청 queue 생성
  - 로봇 profile/learning/dashboard 관리
  - ops-tick 판단 제공

기존 게임서버
  - queue에서 pending 요청 poll
  - 서버 IdFactory로 objectId 발급
  - 서버 DB에 robot/character insert
  - inventory/skill 지급
  - World에 객체 등록
  - AI scheduler 등록
  - tick마다 AIA에 상태 전송 후 판단 수신
```

## 2. 작업 순서 요약

```text
1. AIA 설치
2. .env 설정
3. MySQL 5.5 SQL 적용
4. AIA 실행
5. POST /robot/spawn-requests로 생성 요청 적재
6. 기존 게임서버에 integration/java8 파일 복사
7. integration/java8/aia-server.properties.example을 config/aia-server.properties로 복사 후 수정
8. 기존 서버 시작 루틴에 AiaServerConnector.fromFile() 연결
9. 기존 서버 코드에 MyServerAiaRobotAdapter 구현
10. 기존 로봇 AI tick 또는 NPC/robot update loop에서 connector.opsTick() 호출
11. dashboard로 pending/failed/done 상태 확인
```

## 3. AIA 설치

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

## 4. `.env` 설정

기본 local 설정:

```env
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8000
ENABLE_API_KEY_AUTH=false
DB_BRIDGE_BACKEND=mysql
DB_BRIDGE_MYSQL_DSN=mysql+pymysql://root:password@127.0.0.1:3306/your_game_db
STATE_STORE_MODE=memory
```

외부 IP/LAN에 열 경우:

```env
ENABLE_API_KEY_AUTH=true
API_KEY=충분히_긴_랜덤_키
```

Java 쪽 `config/aia-server.properties`의 `aia.apiKey`에도 같은 값을 넣습니다.

## 5. MySQL 5.5 SQL 적용

AIA 기본 테이블:

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
```

로봇 생성 요청 큐:

```bash
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

확인:

```http
GET /health/details
```

정상:

```text
mysql.status = ok
mysql.missing_tables = []
```

## 6. AIA 실행

```bash
python runners/server/run_local_aia.py
```

확인:

```http
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/health/details
```

## 7. 로봇 생성 요청 넣기

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
  "priority": 100,
  "default_x": 32670,
  "default_y": 32790,
  "default_map": 4,
  "metadata": {
    "memo": "server bootstrap robots"
  }
}
```

`server_name`은 `config/aia-server.properties`의 `aia.serverName`과 반드시 같아야 합니다.

```properties
aia.serverName=main
```

## 8. 기존 게임서버에 복사할 Java 파일

기존 서버 소스 트리에 아래 파일을 복사합니다.

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaServerConfig.java
integration/java8/AiaServerConnector.java
integration/java8/AiaRobotSpawnRequest.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnPoller.java
integration/java8/AiaDecisionParser.java
integration/java8/DbDecisionPoller.java
```

외부 설정 예시 파일은 서버 설정 폴더로 복사합니다.

```text
integration/java8/aia-server.properties.example -> config/aia-server.properties
```

권장 위치 예:

```text
server/src/integration/java8/
server/config/aia-server.properties
```

또는 기존 서버 패키지 정책에 맞춰 다음처럼 옮겨도 됩니다.

```text
server/src/l1j/server/aia/
server/config/aia-server.properties
```

패키지를 바꿀 경우 Java 파일 상단의 package도 같이 바꿔야 합니다.

## 9. 외부 설정 파일 작성

`config/aia-server.properties`:

```properties
# AIA HTTP server
aia.baseUrl=http://127.0.0.1:8000
aia.apiKey=

# Game DB that contains aia_robot_spawn_request
aia.jdbcUrl=jdbc:mysql://127.0.0.1:3306/your_game_db?useUnicode=true&characterEncoding=utf8
aia.dbUser=root
aia.dbPassword=password

# Must match POST /robot/spawn-requests server_name
aia.serverName=main

# Spawn queue polling options
aia.spawnBatchSize=20
aia.healthCheckBeforeSpawn=true

# HTTP timeouts
aia.connectTimeoutMs=3000
aia.readTimeoutMs=5000
```

운영 중 변경 가능성이 큰 값은 모두 이 파일에서 수정합니다.

```text
AIA URL
API key
DB URL
DB user/password
serverName
batch size
timeout
health check 여부
```

## 10. 기존 서버 시작 루틴에 넣는 위치

AIA spawn connector는 서버가 DB와 월드 기본 로딩을 끝낸 뒤 실행해야 합니다.

권장 위치:

```text
GameServer.start()
  -> Config.load()
  -> DatabaseFactory.init()
  -> IdFactory.load()
  -> MapTable.load()
  -> NpcTable.load()
  -> ItemTable.load()
  -> SkillTable.load()
  -> World 초기화
  -> AIA connector bootSpawnOnce 실행
  -> acceptor/listener open
  -> game loop start
```

즉, 아래보다 뒤에 둡니다.

```text
DB 연결 완료 후
IdFactory 준비 후
맵 로드 완료 후
NPC/아이템/스킬 테이블 로드 후
World singleton 준비 후
```

아래보다 앞에 두는 것을 권장합니다.

```text
외부 유저 접속 허용 전
전체 게임 루프 완전 시작 전
```

## 11. 기존 서버에 Bootstrap 클래스 작성

기존 게임서버 안에 예를 들어 아래 파일을 만듭니다.

```text
server/src/.../aia/MyServerAiaBootstrap.java
```

예시:

```java
import integration.java8.AiaServerConnector;

public final class MyServerAiaBootstrap {
    private static AiaServerConnector connector;

    private MyServerAiaBootstrap() {
    }

    public static void bootOnce() {
        try {
            connector = AiaServerConnector.fromFile(
                    "config/aia-server.properties",
                    new MyServerAiaRobotAdapter()
            );
            int processed = connector.bootSpawnOnce();
            System.out.println("[AIA] spawned or processed robots=" + processed);
        } catch (Exception e) {
            System.out.println("[AIA] boot failed: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public static AiaServerConnector getConnector() {
        return connector;
    }
}
```

## 12. 기존 `GameServer.start()`에 호출 추가

예시입니다. 실제 클래스명은 서버마다 다릅니다.

```java
public class GameServer {
    public void start() throws Exception {
        loadConfig();
        initDatabase();
        loadIdFactory();
        loadMaps();
        loadNpc();
        loadItems();
        loadSkills();
        initWorld();

        // AIA 추가 위치
        MyServerAiaBootstrap.bootOnce();

        startLoginServer();
        startGameLoop();
    }
}
```

이미 서버에 `Server`, `L1Server`, `GameServer`, `LoginController`, `GeneralThreadPool` 같은 시작 클래스가 있다면, 위 순서와 가장 가까운 위치에 넣습니다.

## 13. 기존 서버에 Adapter 클래스 작성

파일 예:

```text
server/src/.../aia/MyServerAiaRobotAdapter.java
```

기본 골격:

```java
import integration.java8.AiaRobotSpawnAdapter;
import integration.java8.AiaRobotSpawnRequest;

public class MyServerAiaRobotAdapter implements AiaRobotSpawnAdapter {
    public boolean exists(AiaRobotSpawnRequest request) throws Exception {
        // agent_id 또는 name 기준으로 이미 생성된 로봇인지 확인
        // 예: RobotTable.findByAgentId(request.agentId) != null
        // 예: CharacterTable.doesCharNameExist(request.name)
        return false;
    }

    public long createAndSpawn(AiaRobotSpawnRequest request) throws Exception {
        // 1. objectId 발급
        // 2. 로봇 객체 생성
        // 3. DB insert
        // 4. inventory/skill 지급
        // 5. 좌표/맵/heading 설정
        // 6. World 등록
        // 7. AI scheduler 등록
        // 8. objectId 반환
        return 0L;
    }

    public void afterSpawn(AiaRobotSpawnRequest request, long serverObjectId) throws Exception {
        // 로그, 브로드캐스트, 추가 초기화
    }
}
```

## 14. `exists()`에는 무엇을 작성해야 하나

목적은 중복 생성 방지입니다.

기존 서버에 아래 중 하나가 있으면 사용합니다.

```text
캐릭터 이름 중복 검사
로봇 이름 중복 검사
agent_id metadata 검사
objectId 검사
```

예시:

```java
public boolean exists(AiaRobotSpawnRequest request) throws Exception {
    if (request == null) {
        return true;
    }

    if (CharacterTable.getInstance().doesCharNameExist(request.name)) {
        return true;
    }

    if (RobotTable.getInstance().findByAgentId(request.agentId) != null) {
        return true;
    }

    return false;
}
```

서버에 `agent_id` 컬럼이 없다면 우선 name 기준 중복만 막고, 추후 robot metadata/table에 `agent_id`를 추가하는 것이 좋습니다.

## 15. `createAndSpawn()`에는 무엇을 작성해야 하나

아래 7단계를 기존 서버 코드에 맞춰 연결합니다.

### 15-1. objectId 발급

기존 서버 IdFactory를 사용합니다.

```java
int objectId = IdFactory.getInstance().nextId();
```

또는 서버가 사용하는 실제 방식으로 바꿉니다.

```java
int objectId = ObjectIdFactory.nextId();
```

### 15-2. 로봇/캐릭터 객체 생성

기존 서버의 PC/Robot 클래스에 맞춥니다.

```java
L1RobotInstance robot = new L1RobotInstance();
robot.setId(objectId);
robot.setName(request.name);
robot.setX(request.locX);
robot.setY(request.locY);
robot.setMap((short) request.locMap);
robot.setHeading(request.heading);
robot.setLevel(request.level);
```

서버가 `L1PcInstance` 기반 로봇을 사용한다면:

```java
L1PcInstance robot = new L1PcInstance();
robot.setId(objectId);
robot.setName(request.name);
robot.setX(request.locX);
robot.setY(request.locY);
robot.setMap((short) request.locMap);
robot.setHeading(request.heading);
```

### 15-3. class type 매핑

AIA request의 `classType` / `classId`를 서버 class id로 변환합니다.

```java
private int toServerClassId(AiaRobotSpawnRequest request) {
    if ("royal".equals(request.classType)) return 0;
    if ("knight".equals(request.classType)) return 1;
    if ("elf".equals(request.classType)) return 2;
    if ("wizard".equals(request.classType)) return 3;
    return request.classId;
}
```

서버마다 class id가 다르면 여기만 바꿉니다.

### 15-4. DB insert

기존 서버가 사용하는 저장 함수를 호출합니다.

```java
RobotTable.getInstance().insert(robot);
CharacterTable.getInstance().storeNewCharacter(robot);
```

직접 SQL을 쓰는 서버라면, 기존 insert SQL과 같은 컬럼을 사용해야 합니다.

중요:

```text
AIA queue table에 insert하는 것이 아닙니다.
기존 서버의 robot/characters 테이블에 insert해야 합니다.
서버가 로그인/월드에서 읽는 테이블과 동일해야 합니다.
```

### 15-5. 기본 아이템/스킬 지급

기존 서버 함수 사용:

```java
RobotInventoryFactory.giveBasicItems(robot);
RobotSkillFactory.giveBasicSkills(robot, request.classType);
```

없으면 최소한 아래를 보장합니다.

```text
무기 1개
방어구 기본값
HP potion
귀환/이동 수단
클래스별 기본 skill
```

### 15-6. World 등록

기존 서버 World 등록 함수를 호출합니다.

```java
World.getInstance().storeObject(robot);
World.getInstance().addVisibleObject(robot);
```

또는 서버 방식에 따라:

```java
L1World.getInstance().storeObject(robot);
L1World.getInstance().addVisibleObject(robot);
```

### 15-7. AI scheduler 등록

기존 로봇 AI 실행기에 등록합니다.

```java
RobotAiScheduler.getInstance().register(robot);
```

또는 thread pool 방식이면:

```java
GeneralThreadPool.getInstance().schedule(new RobotAiTask(robot), 1000L);
```

### 15-8. 최종 반환

```java
return objectId;
```

## 16. Adapter 전체 예시

아래는 그대로 복붙 완성 코드가 아니라, 기존 서버 함수명에 맞춰 바꿔야 하는 연결 예시입니다.

```java
import integration.java8.AiaRobotSpawnAdapter;
import integration.java8.AiaRobotSpawnRequest;

public class MyServerAiaRobotAdapter implements AiaRobotSpawnAdapter {
    public boolean exists(AiaRobotSpawnRequest request) throws Exception {
        if (request == null) {
            return true;
        }
        if (CharacterTable.getInstance().doesCharNameExist(request.name)) {
            return true;
        }
        return RobotTable.getInstance().findByAgentId(request.agentId) != null;
    }

    public long createAndSpawn(AiaRobotSpawnRequest request) throws Exception {
        int objectId = IdFactory.getInstance().nextId();

        L1RobotInstance robot = new L1RobotInstance();
        robot.setId(objectId);
        robot.setName(request.name);
        robot.setLevel(request.level);
        robot.setClassId(toServerClassId(request));
        robot.setX(request.locX);
        robot.setY(request.locY);
        robot.setMap((short) request.locMap);
        robot.setHeading(request.heading);
        robot.setAgentId(request.agentId);
        robot.setAiRole(request.role);
        robot.setAiStyle(request.style);

        CharacterTable.getInstance().storeNewCharacter(robot);
        RobotTable.getInstance().insert(robot);

        RobotInventoryFactory.giveBasicItems(robot);
        RobotSkillFactory.giveBasicSkills(robot, request.classType);

        L1World.getInstance().storeObject(robot);
        L1World.getInstance().addVisibleObject(robot);

        RobotAiScheduler.getInstance().register(robot);
        return objectId;
    }

    public void afterSpawn(AiaRobotSpawnRequest request, long serverObjectId) throws Exception {
        System.out.println("[AIA] spawned robot name=" + request.name + " objectId=" + serverObjectId);
    }

    private int toServerClassId(AiaRobotSpawnRequest request) {
        if ("royal".equals(request.classType)) return 0;
        if ("knight".equals(request.classType)) return 1;
        if ("elf".equals(request.classType)) return 2;
        if ("wizard".equals(request.classType)) return 3;
        return request.classId;
    }
}
```

## 17. 로봇 AI tick에 AIA 판단 붙이는 위치

기존 서버에 로봇 AI loop가 있을 가능성이 큽니다.

예상 위치:

```text
RobotAI.run()
RobotController.tick()
RobotInstance.onAiTick()
NpcAIThread.run()
GeneralThreadPool scheduled task
```

기존 로봇 AI tick 안에서 다음 순서로 붙입니다.

```text
1. 서버 로봇 객체 상태 수집
2. AIA ops-tick JSON 생성
3. MyServerAiaBootstrap.getConnector().opsTick(json) 호출
4. AiaDecisionParser로 action 파싱
5. 서버 자체 검증
6. 기존 move/attack/skill 함수 호출
```

예시:

```java
public void onRobotAiTick(L1RobotInstance robot) {
    try {
        AiaServerConnector connector = MyServerAiaBootstrap.getConnector();
        if (connector == null) {
            robot.doIdle();
            return;
        }

        String json = buildOpsTickJson(robot);
        String response = connector.opsTick(json);
        AiaDecision decision = AiaDecisionParser.parse(response);

        if (!isDecisionAllowed(robot, decision)) {
            return;
        }

        executeDecision(robot, decision);
    } catch (Exception e) {
        robot.doIdle();
    }
}
```

## 18. ops-tick JSON 생성 위치

서버 로봇 객체에서 현재 상태를 읽어 JSON을 만듭니다.

```java
private String buildOpsTickJson(L1RobotInstance robot) {
    return "{"
        + "\"observe\":{"
        + "\"agent_id\":\"" + robot.getAgentId() + "\","
        + "\"tick\":" + System.currentTimeMillis() + ","
        + "\"state\":{"
        + "\"hp\":" + robot.getCurrentHp() + ","
        + "\"mp\":" + robot.getCurrentMp() + ","
        + "\"x\":" + robot.getX() + ","
        + "\"y\":" + robot.getY() + ","
        + "\"map_id\":" + robot.getMapId() + ","
        + "\"target_id\":" + jsonString(robot.getTargetId()) + ","
        + "\"target_distance\":" + robot.getTargetDistance() + ","
        + "\"is_under_attack\":" + robot.isUnderAttack() + ","
        + "\"nearby_enemies\":" + robot.countNearbyEnemies() + ","
        + "\"nearby_allies\":" + robot.countNearbyAllies() + ","
        + "\"safe_zone\":" + robot.isSafetyZone() + ","
        + "\"can_teleport\":" + robot.canTeleport() + ","
        + "\"must_use_hp_item\":" + (robot.getCurrentHpPercent() < 35) + ","
        + "\"weight_percent\":" + robot.getWeightPercent()
        + "}"
        + "},"
        + "\"include_dashboard\":false"
        + "}";
}
```

실제 서버에서는 문자열 직접 조립보다 기존 JSON 라이브러리가 있으면 그것을 사용합니다.

## 19. AIA 결정 실행 위치

AIA 응답은 서버에서 반드시 검증한 뒤 실행합니다.

```java
private void executeDecision(L1RobotInstance robot, AiaDecision decision) {
    String action = decision.getAction();

    if ("MOVE".equals(action)) {
        robotMoveService.move(robot, decision.getArgs());
        return;
    }

    if ("ATTACK".equals(action)) {
        robotAttackService.attack(robot, decision.getArgs());
        return;
    }

    if ("USE_SKILL".equals(action)) {
        robotSkillService.useSkill(robot, decision.getArgs());
        return;
    }

    if ("RETREAT".equals(action)) {
        robotMoveService.returnHome(robot);
        return;
    }

    if ("PICKUP".equals(action)) {
        robotItemService.pickupNearby(robot);
        return;
    }

    robot.doIdle();
}
```

검증 예:

```java
private boolean isDecisionAllowed(L1RobotInstance robot, AiaDecision decision) {
    if (decision == null) return false;
    if (robot.isDead()) return false;
    if ("ATTACK".equals(decision.getAction()) && robot.getTarget() == null) return false;
    if ("USE_SKILL".equals(decision.getAction()) && robot.isSkillDelay()) return false;
    if ("MOVE".equals(decision.getAction()) && robot.isParalyzed()) return false;
    return true;
}
```

## 20. 실패/복구 확인

GUI:

```http
GET /dashboard/robot-spawn-queue/gui?server_name=main
GET /dashboard/robot-spawn-queue/gui?status=failed&server_name=main
```

실패 재시도:

```http
POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50
```

오래된 claimed 복구:

```http
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

## 21. 운영 설정 실시간 반영

아래 JSON은 AIA 재시작 없이 다음 요청에서 자동 반영됩니다.

```text
app/config/robot_autonomy_defaults.json
app/config/aia_robot_top_profile.json
```

확인:

```http
GET /dashboard/robot-autonomy-baseline
```

`live_reload.enabled = true`이면 정상입니다.

## 22. 테스트

전체:

```bash
python runners/quality/run_quality_gates.py
```

주요 개별:

```bash
pytest tests/test_mods.py
pytest tests/test_auto_live.py
pytest tests/test_spawn_api.py
pytest tests/test_spawn_dash.py
pytest tests/test_spawn_ui.py
pytest tests/test_mysql55.py
```

MySQL 통합:

```bash
AIA_TEST_MYSQL_DSN=mysql+pymysql://root:root@127.0.0.1:3306/aia_ci \
python -m pytest tests/test_mysql_spawn_queue_integration.py
```

## 23. 자주 나는 문제

### pending에서 멈춤

확인:

```text
server_name이 AIA 요청과 Java connector에서 같은가?
AiaServerConnector.bootSpawnOnce()가 호출되는가?
DB 계정이 aia_robot_spawn_request update 권한을 갖는가?
```

### claimed에서 멈춤

Adapter에서 예외가 나거나 서버가 중간 종료된 경우입니다.

```http
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

### failed가 발생

GUI에서 `last_error`를 확인합니다.

```http
GET /dashboard/robot-spawn-queue/gui?status=failed&server_name=main
```

대부분 아래 원인입니다.

```text
중복 이름
IdFactory 미초기화
맵 좌표 오류
DB insert 컬럼 누락
World 등록 전 객체 필드 부족
AI scheduler 등록 실패
```

### 로봇은 생성됐는데 움직이지 않음

확인:

```text
AI scheduler 등록 여부
tick loop 실행 여부
connector.opsTick() 호출 여부
AIA 응답 action 파싱 여부
서버 최종 검증에서 막히는지 여부
```

## 24. 현재 AIA 공식 파일 구조

```text
app/models/req.py
app/models/res.py
app/models/dash.py
app/models/uni.py
app/models/auto.py
app/models/batch.py

app/services/spawn.py
app/services/spawn_dash.py
app/services/autonomy.py
app/ui/spawn_queue.py
```
