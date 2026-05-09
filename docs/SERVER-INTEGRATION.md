# 서버 연동 계약

이 문서는 게임서버 개발자가 AIA를 붙일 때 구현해야 할 코드 계약만 정리합니다. 설치/실행 순서는 `docs/USAGE.md`를 봅니다.

## 1. 절대 원칙

AIA는 서버 원본 `robot`, `characters`, `robot_setting` 테이블을 직접 수정하지 않습니다.

```text
AIA가 하는 일
- spawn request 생성
- profile 등록
- observe/decide/ops-tick 판단
- feedback/learning 저장
- dashboard 제공

게임서버가 하는 일
- objectId 발급
- 서버 원본 DB insert/update/delete
- world spawn/despawn
- inventory/skill 지급
- 이동/공격/스킬 실제 실행
```

## 2. Spawn Request Queue

AIA는 `aia_robot_spawn_request`에 요청만 넣습니다.

```text
pending -> claimed -> done
pending -> claimed -> failed
failed  -> pending retry 가능
claimed stale -> pending recovery 가능
```

SQL:

```bash
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

AIA 요청 생성:

```http
POST /robot/spawn-requests
```

## 3. Java 8 필수 파일

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaRobotSpawnRequest.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnPoller.java
```

서버에 위 파일을 복사하거나 같은 패키지 규칙에 맞게 이동합니다.

## 4. AiaRobotSpawnAdapter 구현 계약

```java
public interface AiaRobotSpawnAdapter {
    boolean exists(AiaRobotSpawnRequest request) throws Exception;
    long createAndSpawn(AiaRobotSpawnRequest request) throws Exception;
    void afterSpawn(AiaRobotSpawnRequest request, long serverObjectId) throws Exception;
}
```

### exists

중복 생성을 막습니다.

권장 확인 기준:

```text
agent_id
name
server robot uid
objectId metadata
```

### createAndSpawn

서버의 실제 로봇 생성 로직을 여기에 연결합니다.

필수 처리:

```text
1. IdFactory에서 objectId 발급
2. 서버 원본 robot/character 테이블 insert
3. level/class/name/heading/x/y/map 반영
4. inventory 기본 지급
5. skill 기본 지급
6. World store/add visible object
7. AI scheduler 등록
8. 생성된 objectId 또는 robot uid 반환
```

### afterSpawn

선택 처리:

```text
운영 로그
GM 알림
월드 브로드캐스트
추가 버프/상태 초기화
```

## 5. 서버 시작 루틴 연결 위치

권장 위치:

```text
DB 로드 완료 후
맵/NPC 로드 완료 후
월드 객체 등록 가능 상태 후
게임 루프 시작 전
```

예:

```text
Server.start()
  -> loadDatabase()
  -> loadWorld()
  -> loadNpc()
  -> runAiaRobotSpawnPoller()
  -> startGameLoop()
```

## 6. Poller 예시

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

## 7. 판단 루프 계약

생성된 로봇은 tick마다 AIA에 상태를 보냅니다.

```http
POST /api/v1/robot/ops-tick
```

AIA 응답은 권고입니다. 서버가 최종 검증해야 합니다.

```text
맵 일치
이동 가능 타일
타겟 생존
거리 조건
스킬 쿨타임
HP/MP/무게
안전지대 전투 금지
```

## 8. 실패 처리

Spawn queue GUI:

```http
GET /dashboard/robot-spawn-queue/gui
GET /dashboard/robot-spawn-queue/gui?status=failed
```

재시도:

```http
POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50
```

오래된 claimed 복구:

```http
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

## 9. MySQL 5.5 주의사항

```text
charset=utf8 사용
JSON column 사용 금지
generated column 사용 금지
JDBC characterEncoding=utf8 사용
```

## 10. 구현 완료 기준

```text
pending 요청이 claimed로 변경된다.
성공 시 done이 된다.
실패 시 failed와 last_error가 남는다.
생성된 로봇이 월드에 보인다.
AIA /robot 목록에 profile이 등록된다.
/dashboard/robot-spawn-queue/gui에서 상태가 보인다.
ops-tick 판단 결과를 서버가 검증 후 실행한다.
```
