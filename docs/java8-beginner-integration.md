# Java 8 Beginner Integration Guide

## 목적
초보자도 AIA를 Java 8 게임서버에 붙일 수 있도록, 어떤 클래스를 어디에 두고 무엇을 수정해야 하는지 단계별로 설명합니다.

## 새로 추가된 Java 클래스
- `integration/java8/AiaDecision.java`
- `integration/java8/AiaDecisionParser.java`
- `integration/java8/LocalAiaClient.java`
- `integration/java8/RobotStateExtractor.java`
- `integration/java8/RobotActionExecutor.java`
- `integration/java8/RobotStateWriter.java`
- `integration/java8/RobotEventWriter.java`
- `integration/java8/RobotFeedbackWriter.java`
- `integration/java8/DbDecisionPoller.java`

## 각 클래스 역할
### AiaDecision
AIA 응답 한 건을 담는 모델입니다.

### AiaDecisionParser
`/decide` 응답 JSON에서 action, confidence, reason 등을 읽습니다.

### LocalAiaClient
로컬 AIA 서버(`127.0.0.1:8000`)에 HTTP POST를 보냅니다.

### RobotStateExtractor
현재 서버 캐릭터 객체에서 상태를 읽어 AIA 요청 JSON을 만듭니다.
가장 먼저 수정해야 할 파일입니다.

### RobotActionExecutor
AIA가 반환한 action을 실제 이동/공격/스킬/귀환 함수로 연결합니다.
처음에는 println으로 테스트하고, 나중에 실제 서버 함수로 바꿉니다.

### RobotStateWriter
현재 상태를 `robot_state` 테이블에 기록합니다.

### RobotEventWriter
중요 이벤트를 `robot_event` 테이블에 기록합니다.

### RobotFeedbackWriter
행동 결과를 `robot_feedback` 테이블에 기록합니다.
학습/성장에 필요합니다.

### DbDecisionPoller
DB 중심 혼합형에서 최신 decision action을 읽습니다.

## 초보자 추천 순서
1. `RobotStateExtractor`의 TODO를 수정
2. `LocalAiaClient`로 `/health`, `/decide` 호출 확인
3. `RobotActionExecutor`를 println으로 먼저 확인
4. `RobotStateWriter`로 상태 저장 확인
5. `RobotFeedbackWriter`로 결과 저장 확인
6. 로봇 루프에 위 4개를 연결

## 실제 수정이 필요한 부분
### 1. RobotStateExtractor
- agentId
- hp/mp
- x/y
- mapId
- targetId
- targetDistance
- safeZone
- weightPercent
- potionCount
- underAttack
- canTeleport

이 값들을 현재 서버의 getter로 바꾸면 됩니다.

### 2. RobotActionExecutor
다음 TODO를 현재 서버 함수에 연결합니다.
- MOVE
- ATTACK
- USE_SKILL
- RETREAT
- PICKUP

### 3. JDBC 설정
다음 값만 현재 DB로 바꾸면 됩니다.
- jdbcUrl
- user
- password

## 가장 쉬운 테스트 방식
### 1단계
AIA를 먼저 실행합니다.
```bash
python one_click_start.py
```

### 2단계
Java 8 서버에서 `LocalAiaClient`로 `/decide` 호출만 해봅니다.

### 3단계
응답 action을 `RobotActionExecutor`에서 println으로 출력해봅니다.

### 4단계
정상 확인 후 실제 이동/공격 함수로 교체합니다.

## 초보자 핵심 팁
- 처음부터 완벽하게 하려고 하지 마세요.
- 먼저 상태 추출 3개(hp/mp/x/y)만 넣어도 됩니다.
- 처음엔 실행기에서 println만 하세요.
- 그 다음 DB 저장을 붙이세요.
- 마지막에 실제 서버 행동 함수로 연결하세요.
