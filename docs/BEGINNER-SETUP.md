# AIA 초보자 완전 구성 가이드

이 문서는 서버에 로봇 코드/테이블이 전혀 없는 상태에서 AIA를 붙이는 순서를 설명합니다.

목표는 아래 상태까지 만드는 것입니다.

```text
1. AIA 실행
2. MySQL 5.5 테이블 생성
3. 기본 로봇 생성요청 6개 적재
4. Java connector가 pending 요청 처리
5. robot / robot_item / robot_skill / robot_ai / robot_log 테이블 생성 확인
6. 기존 서버 World 등록과 AI tick 연결 준비
```

## 1. 전체 구성 그림

```text
AIA Python Server
  └─ POST /robot/spawn-requests
      └─ aia_robot_spawn_request 에 pending 생성

Java Game Server
  └─ AiaServerConnector.bootSpawnOnce()
      ├─ aia_robot_spawn_request pending -> claimed
      ├─ BasicRobotAdapter.createAndSpawn()
      ├─ RobotStore.createRobot()
      ├─ robot / robot_item / robot_skill / robot_ai / robot_log insert
      └─ pending row -> done 또는 failed
```

중요 원칙:

```text
AIA는 robot 테이블에 직접 insert하지 않습니다.
AIA는 aia_robot_spawn_request에 생성요청만 넣습니다.
실제 로봇 생성은 Java 서버 Adapter가 처리합니다.
```

## 2. 필요한 파일

### SQL

```text
sql/aia_robot_schema.sql
sql/aia_robot_spawn_request_mysql55.sql
sql/robot_min_mysql55.sql
sql/robot_seed_mysql55.sql
```

### Java

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaServerConfig.java
integration/java8/AiaServerConnector.java
integration/java8/AiaRobotTemplateConfig.java
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

### 설정

```text
integration/java8/aia-server.properties.example
integration/java8/aia-robot-template.properties.example
```

## 3. DB 적용 순서

아래 순서 그대로 적용합니다.

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
mysql -u root -p your_game_db < sql/robot_min_mysql55.sql
mysql -u root -p your_game_db < sql/robot_seed_mysql55.sql
```

각 파일 역할:

| 파일 | 역할 |
|---|---|
| `aia_robot_schema.sql` | AIA 상태/이벤트/학습/판단 관련 테이블 생성 |
| `aia_robot_spawn_request_mysql55.sql` | 로봇 생성 요청 queue 생성 |
| `robot_min_mysql55.sql` | 로봇이 없는 서버용 최소 robot 테이블 생성 |
| `robot_seed_mysql55.sql` | 초보자 테스트용 pending 생성요청 6개 적재 |

## 4. 생성되는 테이블

### AIA 전용 테이블

```text
aia_robot_state
aia_robot_event
aia_robot_issue
aia_robot_learning
aia_robot_stall
aia_robot_autofix
aia_robot_metric
aia_world_hunt_guide
aia_world_siege_guide
aia_robot_feedback
aia_robot_decision
aia_robot_trace_summary
aia_robot_spawn_request
```

### 서버 로봇 최소 테이블

```text
robot
robot_item
robot_skill
robot_ai
robot_log
```

## 5. 최소 robot 테이블 내용

### `robot`

로봇 기본 정보입니다.

주요 컬럼:

| 컬럼 | 설명 |
|---|---|
| `robot_uid` | DB 내부 로봇 번호 |
| `object_id` | 서버 IdFactory에서 발급한 객체 ID |
| `agent_id` | AIA 로봇 식별자 |
| `name` | 로봇 이름 |
| `class_type` | royal/knight/elf/wizard 등 |
| `class_id` | 서버 클래스 ID |
| `level` | 레벨 |
| `hp`, `max_hp` | HP |
| `mp`, `max_mp` | MP |
| `loc_x`, `loc_y`, `loc_map` | 현재 좌표 |
| `home_x`, `home_y`, `home_map` | 기준 좌표 |
| `role` | 역할 |
| `style` | 행동 스타일 |
| `ai_enabled` | AI 사용 여부 |
| `deleted` | 삭제 여부 |

### `robot_item`

로봇 기본 아이템입니다.

| 컬럼 | 설명 |
|---|---|
| `robot_uid` | robot 테이블의 로봇 번호 |
| `object_id` | 서버 객체 ID |
| `item_id` | 서버 아이템 ID |
| `count` | 수량 |
| `equipped` | 착용 여부 |
| `enchant_level` | 인챈트 |

### `robot_skill`

로봇 기본 스킬입니다.

| 컬럼 | 설명 |
|---|---|
| `robot_uid` | robot 테이블의 로봇 번호 |
| `skill_id` | 서버 스킬 ID |
| `skill_level` | 스킬 레벨 |
| `enabled` | 사용 여부 |

### `robot_ai`

AI runtime 상태입니다.

| 컬럼 | 설명 |
|---|---|
| `current_action` | 현재 행동 |
| `target_id` | 대상 ID |
| `hp_percent` | HP 비율 |
| `mp_percent` | MP 비율 |
| `weight_percent` | 무게 비율 |
| `last_decision` | 마지막 AIA 판단 |
| `last_reason` | 판단 이유 |
| `last_error` | 오류 |
| `last_tick_at` | 마지막 tick 시간 |

### `robot_log`

로봇 로그입니다.

| 컬럼 | 설명 |
|---|---|
| `log_type` | spawn/action/error 등 |
| `message` | 로그 메시지 |
| `loc_x`, `loc_y`, `loc_map` | 로그 발생 위치 |

## 6. 기본 seed 내용

`sql/robot_seed_mysql55.sql`은 `robot` 테이블이 아니라 `aia_robot_spawn_request`에 pending 요청을 넣습니다.

기본 요청 6개:

| request_id | 이름 | class_type | level | 좌표 |
|---|---|---|---:|---|
| seed-main-royal-0001 | AIA군주001 | royal | 10 | 32670,32790,4 |
| seed-main-knight-0001 | AIA기사001 | knight | 10 | 32671,32790,4 |
| seed-main-knight-0002 | AIA기사002 | knight | 8 | 32672,32790,4 |
| seed-main-elf-0001 | AIA요정001 | elf | 10 | 32669,32790,4 |
| seed-main-elf-0002 | AIA요정002 | elf | 8 | 32668,32790,4 |
| seed-main-wizard-0001 | AIA법사001 | wizard | 10 | 32670,32791,4 |

적용 확인:

```sql
SELECT uid, request_id, server_name, agent_id, name, class_type, level, status
FROM aia_robot_spawn_request
WHERE request_id LIKE 'seed-main-%'
ORDER BY uid;
```

정상 상태:

```text
status = pending
```

Java connector가 정상 처리하면:

```text
status = done
```

오류가 있으면:

```text
status = failed
last_error 컬럼 확인
```

## 7. Java 설정 파일 작성

기존 게임서버의 `config/` 폴더에 복사합니다.

```text
config/aia-server.properties
config/aia-robot-template.properties
```

### `config/aia-server.properties`

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

주의:

```text
aia.serverName=main
```

이 값은 `robot_seed_mysql55.sql`의 `server_name='main'`과 같아야 합니다.

### `config/aia-robot-template.properties`

```properties
aia.class.royal=0
aia.class.knight=1
aia.class.elf=2
aia.class.wizard=3
aia.class.default=1

aia.hp.default=100
aia.hp.knight=160
aia.hp.elf=120
aia.hp.wizard=80

aia.mp.default=30
aia.mp.knight=20
aia.mp.elf=60
aia.mp.wizard=120

aia.item.default=40010,40011
aia.item.knight=1,23,40010,40011
aia.item.elf=4,37,40010,40011
aia.item.wizard=7,51,40010,40011

aia.skill.default=
aia.skill.knight=1,2
aia.skill.elf=3,4,5
aia.skill.wizard=6,7,8
```

서버의 실제 classId, itemId, skillId와 다르면 여기만 수정합니다.

## 8. Java Bootstrap 작성

기존 서버에 `MyServerAiaBootstrap.java`를 만듭니다.

```java
import integration.java8.AiaRobotActionRunner;
import integration.java8.AiaRobotTemplateConfig;
import integration.java8.AiaServerConnector;
import integration.java8.BasicRobotAdapter;
import integration.java8.RobotStore;

public final class MyServerAiaBootstrap {
    private static AiaServerConnector connector;
    private static AiaRobotActionRunner actionRunner;

    private MyServerAiaBootstrap() {
    }

    public static void bootOnce() {
        try {
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
            ) {
                protected void afterCreateRows(AiaRobotSpawnRequest request, long robotUid, long objectId) throws Exception {
                    // 초보자 1차 목표: DB row 생성 확인.
                    // 2차 목표: 여기에서 실제 서버 로봇 객체 생성, World 등록, AI scheduler 등록.
                }
            };

            connector = AiaServerConnector.fromFile("config/aia-server.properties", adapter);
            int processed = connector.bootSpawnOnce();
            actionRunner = new AiaRobotActionRunner(connector, new MyServerAiaRobotActionAdapter());
            System.out.println("[AIA] spawn processed=" + processed);
        } catch (Exception e) {
            System.out.println("[AIA] boot failed: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public static AiaRobotActionRunner getActionRunner() {
        return actionRunner;
    }
}
```

## 9. GameServer 시작부에 추가

기존 서버 시작 순서에서 DB, 맵, 월드 로드가 끝난 뒤 넣습니다.

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

## 10. 실행 후 확인

### 10-1. 생성요청 처리 확인

```sql
SELECT request_id, name, class_type, status, attempts, last_error
FROM aia_robot_spawn_request
WHERE request_id LIKE 'seed-main-%'
ORDER BY uid;
```

정상:

```text
status = done
last_error = spawned:<object_id>
```

### 10-2. robot 생성 확인

```sql
SELECT robot_uid, object_id, agent_id, name, class_type, level, loc_x, loc_y, loc_map
FROM robot
ORDER BY robot_uid;
```

### 10-3. 아이템 확인

```sql
SELECT r.name, i.item_id, i.count
FROM robot r
JOIN robot_item i ON r.robot_uid = i.robot_uid
ORDER BY r.robot_uid, i.item_id;
```

### 10-4. 스킬 확인

```sql
SELECT r.name, s.skill_id, s.skill_level
FROM robot r
JOIN robot_skill s ON r.robot_uid = s.robot_uid
ORDER BY r.robot_uid, s.skill_id;
```

### 10-5. AI 상태 확인

```sql
SELECT r.name, a.current_action, a.last_decision, a.last_error, a.last_tick_at
FROM robot r
JOIN robot_ai a ON r.robot_uid = a.robot_uid
ORDER BY r.robot_uid;
```

## 11. 화면에 안 보일 때

DB에는 생성됐지만 게임 화면에 보이지 않으면 아직 World 등록이 빠진 상태입니다.

`BasicRobotAdapter.afterCreateRows()` 안에 서버별 코드를 추가해야 합니다.

필수 작업:

```text
1. 서버 로봇 객체 생성
2. objectId 적용
3. name/class/level/x/y/map/heading 적용
4. World.storeObject 또는 equivalent 호출
5. World.addVisibleObject 또는 equivalent 호출
6. AI scheduler/register 호출
```

## 12. 실패 시 확인

### pending 그대로

```text
AiaServerConnector.bootSpawnOnce()가 호출되지 않았습니다.
aia.serverName 값이 seed의 server_name과 다를 수 있습니다.
DB 계정 권한이 부족할 수 있습니다.
```

### failed

```sql
SELECT request_id, status, attempts, last_error
FROM aia_robot_spawn_request
WHERE status = 'failed'
ORDER BY uid DESC;
```

### robot 중복 오류

이미 seed를 한 번 처리했다면 같은 `agent_id`, `name`은 중복입니다.

재처리하려면 테스트 DB에서만 아래처럼 정리합니다.

```sql
DELETE FROM robot_log;
DELETE FROM robot_ai;
DELETE FROM robot_skill;
DELETE FROM robot_item;
DELETE FROM robot;
UPDATE aia_robot_spawn_request
SET status='pending', attempts=0, last_error='', claimed_at=NULL, done_at=NULL
WHERE request_id LIKE 'seed-main-%';
```

## 13. 초보자 완료 기준

아래가 모두 되면 1차 구성 완료입니다.

```text
AIA /health 정상
SQL 4개 적용 완료
seed-main 요청 6개 pending 확인
서버 시작 시 bootSpawnOnce() 실행
seed-main 요청 done 변경
robot 테이블에 6개 생성
robot_item / robot_skill 생성
robot_ai 생성
```

2차 완료 기준:

```text
afterCreateRows()에서 World 등록
AI scheduler 등록
AiaRobotActionRunner.tick(robot) 호출
move / attack / skill 실행
```
