# AIA 서버 연동 상세 사용방법

이 문서는 기존 Java 게임서버에 AIA를 붙이는 실제 작업 순서를 설명합니다. 핵심은 AIA가 서버 DB에 직접 로봇을 insert하지 않고, 기존 게임서버가 `AiaRobotSpawnAdapter`와 `AiaRobotActionAdapter`를 구현하여 자기 방식대로 로봇을 생성하고 실행하게 하는 것입니다.

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
  - 서버 DB에 robot/robot_item/robot_skill insert
  - World에 객체 등록
  - AI scheduler 등록
  - tick마다 AIA에 상태 전송 후 판단 수신
  - AiaRobotActionAdapter로 move/attack/skill 실행
```

## 2. 작업 순서 요약

```text
1. AIA 설치
2. .env 설정
3. MySQL 5.5 SQL 적용
4. 서버에 로봇 테이블이 없다면 sql/robot_min_mysql55.sql 적용
5. AIA 실행
6. POST /robot/spawn-requests로 생성 요청 적재
7. 기존 게임서버에 integration/java8 파일 복사
8. aia-server.properties와 aia-robot-template.properties를 서버 config에 복사 후 수정
9. 기존 서버 시작 루틴에 AiaServerConnector.fromFile() 연결
10. 기존 서버 코드에 MyServerAiaRobotAdapter 또는 BasicRobotAdapter 기반 Adapter 구현
11. 기존 서버 코드에 MyServerAiaRobotActionAdapter 구현
12. 기존 로봇 AI tick 또는 NPC/robot update loop에서 AiaRobotActionRunner.tick(robot) 호출
13. dashboard로 pending/failed/done 상태 확인
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

기본 AIA 테이블:

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

서버에 로봇 테이블이 전혀 없다면 추가 적용:

```bash
mysql -u root -p your_game_db < sql/robot_min_mysql55.sql
```

생성되는 최소 로봇 테이블:

```text
robot
robot_item
robot_skill
robot_ai
robot_log
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
  "default_map": 4
}
```

`server_name`은 `config/aia-server.properties`의 `aia.serverName`과 반드시 같아야 합니다.

## 8. 기존 게임서버에 복사할 Java 파일

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaServerConfig.java
integration/java8/AiaServerConnector.java
integration/java8/AiaRobotTemplateConfig.java
integration/java8/AiaRobotSpawnRequest.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnPoller.java
integration/java8/AiaDecision.java
integration/java8/AiaDecisionParser.java
integration/java8/AiaRobotActionAdapter.java
integration/java8/AiaRobotActionRunner.java
integration/java8/AiaSpawnQueue.java
integration/java8/JdbcAiaSpawnQueue.java
integration/java8/AiaSpawnQueueSql.java
integration/java8/RobotStore.java
integration/java8/BasicRobotAdapter.java
integration/java8/DbDecisionPoller.java
```

설정 파일:

```text
integration/java8/aia-server.properties.example -> server/config/aia-server.properties
integration/java8/aia-robot-template.properties.example -> server/config/aia-robot-template.properties
```

## 9. 외부 설정 파일 작성

`config/aia-server.properties`:

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

`config/aia-robot-template.properties`:

```properties
aia.class.royal=0
aia.class.knight=1
aia.class.elf=2
aia.class.wizard=3
aia.class.default=1

aia.item.default=40010,40011
aia.item.knight=1,23,40010,40011
aia.item.elf=4,37,40010,40011
aia.item.wizard=7,51,40010,40011

aia.skill.default=
aia.skill.knight=1,2
aia.skill.elf=3,4,5
aia.skill.wizard=6,7,8
```

서버별로 자주 바뀌는 classId, itemId, skillId, HP/MP 기본값은 `aia-robot-template.properties`에서 수정합니다.

## 10. 기존 서버 시작 루틴에 넣는 위치

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

## 11. Bootstrap 클래스 작성

```java
import integration.java8.AiaRobotActionRunner;
import integration.java8.AiaRobotTemplateConfig;
import integration.java8.AiaServerConnector;
import integration.java8.BasicRobotAdapter;
import integration.java8.RobotStore;

public final class MyServerAiaBootstrap {
    private static AiaServerConnector connector;
    private static AiaRobotActionRunner actionRunner;
    private static AiaRobotTemplateConfig template;

    private MyServerAiaBootstrap() {
    }

    public static void bootOnce() {
        try {
            template = AiaRobotTemplateConfig.fromFile("config/aia-robot-template.properties");
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
            connector = AiaServerConnector.fromFile("config/aia-server.properties", adapter);
            int processed = connector.bootSpawnOnce();
            actionRunner = new AiaRobotActionRunner(connector, new MyServerAiaRobotActionAdapter());
            System.out.println("[AIA] spawned or processed robots=" + processed);
        } catch (Exception e) {
            System.out.println("[AIA] boot failed: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public static AiaServerConnector getConnector() {
        return connector;
    }

    public static AiaRobotActionRunner getActionRunner() {
        return actionRunner;
    }

    public static AiaRobotTemplateConfig getTemplate() {
        return template;
    }
}
```

## 12. 기존 `GameServer.start()`에 호출 추가

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

        MyServerAiaBootstrap.bootOnce();

        startLoginServer();
        startGameLoop();
    }
}
```

## 13. Spawn Adapter 구현

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
    }
}
```

서버에 로봇 구조가 전혀 없으면 `BasicRobotAdapter`로 시작하고, `afterCreateRows()`를 override해서 실제 World 등록만 붙입니다.

```java
public class MyRobotAdapter extends BasicRobotAdapter {
    public MyRobotAdapter(RobotStore store, AiaRobotTemplateConfig template, ObjectIdProvider provider) {
        super(store, template, provider);
    }

    protected void afterCreateRows(AiaRobotSpawnRequest request, long robotUid, long objectId) throws Exception {
        // 1. 메모리 로봇 객체 생성
        // 2. request 좌표/레벨/클래스 적용
        // 3. World 등록
        // 4. AI scheduler 등록
    }
}
```

## 14. Action Adapter 구현

```java
import integration.java8.AiaDecision;
import integration.java8.AiaRobotActionAdapter;

public class MyServerAiaRobotActionAdapter implements AiaRobotActionAdapter {
    public String buildOpsTickJson(Object robotObj) throws Exception {
        return "{}";
    }

    public boolean canExecute(Object robotObj, AiaDecision decision) throws Exception {
        return decision != null;
    }

    public void move(Object robot, AiaDecision decision) throws Exception {}
    public void attack(Object robot, AiaDecision decision) throws Exception {}
    public void useSkill(Object robot, AiaDecision decision) throws Exception {}
    public void retreat(Object robot, AiaDecision decision) throws Exception {}
    public void pickup(Object robot, AiaDecision decision) throws Exception {}
    public void idle(Object robot) throws Exception {}
    public void onError(Object robot, Exception error) throws Exception { idle(robot); }
}
```

## 15. 로봇 AI tick에 연결

```java
AiaRobotActionRunner runner = MyServerAiaBootstrap.getActionRunner();
if (runner != null) {
    runner.tick(robot);
    return;
}
```

## 16. 실패/복구 확인

```http
GET /dashboard/robot-spawn-queue/gui?server_name=main
GET /dashboard/robot-spawn-queue/gui?status=failed&server_name=main
POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

## 17. 운영 설정 실시간 반영

아래 JSON은 AIA 재시작 없이 다음 요청에서 자동 반영됩니다.

```text
app/config/robot_autonomy_defaults.json
app/config/aia_robot_top_profile.json
```

확인:

```http
GET /dashboard/robot-autonomy-baseline
```

## 18. 테스트

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

## 19. 자주 나는 문제

### pending에서 멈춤

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

### 로봇은 생성됐는데 움직이지 않음

```text
AI scheduler 등록 여부
tick loop 실행 여부
AiaRobotActionRunner.tick(robot) 호출 여부
AIA 응답 action 파싱 여부
서버 최종 검증에서 막히는지 여부
```
