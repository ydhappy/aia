# 서버 연동 요약

## 원칙

AIA는 서버 원본 `robot`, `characters`, `robot_setting` 같은 테이블을 직접 수정하지 않습니다. AIA는 생성 요청, 프로필, 판단, 학습, 대시보드를 담당하고 게임서버가 실제 객체 생성과 실행을 담당합니다.

```text
AIA: 생성 요청 / 프로필 / 판단 / 학습 / 대시보드
게임서버: objectId / DB insert / world spawn / 이동 / 공격 / 스킬 / 삭제
```

## MySQL 5.5 생성 요청 큐

적용 파일:

```bash
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

이 테이블은 AIA가 로봇 생성 요청만 넣는 안전 큐입니다.

```text
aia_robot_spawn_request.status
- pending: 서버가 처리해야 할 요청
- claimed: 서버가 잡은 요청
- done: 생성 완료
- failed: 생성 실패
```

## AIA에서 생성 요청 만들기

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
  "metadata": {"memo": "auto spawn"}
}
```

## 게임서버 Java 8 연결

주요 파일:

```text
integration/java8/AiaRobotSpawnPoller.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnRequest.java
integration/java8/LocalAiaClient.java
```

서버 시작 루틴 예:

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

서버별로 구현할 부분:

```java
public long createAndSpawn(AiaRobotSpawnRequest request) throws Exception {
    // 1. 서버 IdFactory로 objectId 발급
    // 2. 서버 robot/character 테이블 insert
    // 3. inventory/skill 지급
    // 4. World 등록
    // 5. AI scheduler 등록
    // 6. objectId 반환
}
```

## Spawn Queue 운영

```http
GET  /dashboard/robot-spawn-queue
GET  /dashboard/robot-spawn-queue/gui
GET  /dashboard/robot-spawn-queue/gui?status=failed
POST /dashboard/robot-spawn-queue/retry-failed?server_name=main&limit=50
POST /dashboard/robot-spawn-queue/recover-claimed?server_name=main&older_than_minutes=10&limit=50
```

## 로봇 판단 루프

생성 후 매 tick 서버가 AIA에 상태를 보내고 응답을 검증 후 실행합니다.

```http
POST /api/v1/robot/ops-tick
```

서버는 반드시 다음을 최종 검증합니다.

```text
맵 일치
이동 가능 타일
타겟 생존
거리/쿨타임
안전지대 전투 금지
HP/MP/무게 조건
```
