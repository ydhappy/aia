# AIA 제3자 관점 점검 보고서

이 문서는 AIA를 처음 보는 외부 운영자/개발자 관점에서 현재 구조를 점검한 결과입니다.

## 결론

AIA는 현재 게임서버에 직접 로봇을 생성하지 않고, MySQL 큐와 Java 8 poller/adapter 계약을 통해 서버가 직접 로봇을 생성하도록 분리되어 있습니다. 이 방향은 안전합니다. 특히 서버 원본 DB 테이블을 AIA가 직접 수정하지 않는 구조는 유지해야 합니다.

## 긍정 평가

- 순수 코드와 실행 코드가 분리되어 있습니다.
- 예제/샘플 전용 코드가 제거되어 운영 코드 경계가 명확합니다.
- MySQL 5.5 호환 SQL을 별도 파일로 유지합니다.
- Java 8 연동 코드는 `integration/java8/`에 모여 있습니다.
- Spawn Queue는 `pending/claimed/done/failed` 상태를 명확히 가집니다.
- Spawn Queue Dashboard는 `server_name` 필터를 지원합니다.
- 복구 API는 `server_name` 단위로 실행됩니다.
- `/health/details`에서 MySQL 연결과 필수 테이블 존재 여부를 확인할 수 있습니다.
- GitHub Actions에서 기본 품질 게이트와 MariaDB 통합 테스트를 실행합니다.
- `runners/quality/run_quality_gates.py`와 `.ps1`로 로컬/CI 테스트 경로가 분리되어 있습니다.

## 현재 운영 전 필수 확인

### 1. 인증

`.env.example`은 local 기준입니다. LAN 또는 public IP에 노출할 경우 반드시 다음을 적용해야 합니다.

```env
ENABLE_API_KEY_AUTH=true
API_KEY=충분히_긴_랜덤_키
```

그리고 Java client에도 같은 API key를 넣어야 합니다.

### 2. 바인딩 주소

local 테스트는 다음이 안전합니다.

```env
APP_HOST=127.0.0.1
```

외부 접속이 필요해 `0.0.0.0`을 사용할 경우 API key 인증을 켜야 합니다.

### 3. DB SQL 적용

필수 SQL:

```bash
mysql -u root -p your_game_db < sql/aia_robot_schema.sql
mysql -u root -p your_game_db < sql/aia_robot_spawn_request_mysql55.sql
```

적용 후 확인:

```http
GET /health/details
```

`mysql.missing_tables`가 빈 배열이어야 합니다.

### 4. 서버별 Queue 확인

여러 게임서버가 같은 AIA DB를 사용할 경우 반드시 `server_name` 필터를 적용해서 봅니다.

```http
GET /dashboard/robot-spawn-queue?server_name=main
GET /dashboard/robot-spawn-queue/gui?server_name=main
GET /dashboard/robot-spawn-queue/gui?status=failed&server_name=main
```

복구 버튼도 현재 server_name 기준으로 실행합니다.

### 5. Java Adapter 구현

`integration/java8/AiaRobotSpawnAdapter.java`는 계약입니다. 실제 서버에서는 반드시 다음을 서버 코드에 연결해야 합니다.

- 서버 IdFactory
- 로봇/캐릭터 DB insert
- 기본 아이템/스킬 지급
- World spawn
- AI scheduler 등록
- 중복 agent/name 검사

## 주요 리스크와 권장 대응

### R1. 인증 비활성 상태로 외부 노출

위험도: 높음

대응:

- local이 아니면 `ENABLE_API_KEY_AUTH=true` 강제.
- `/health/details.security.warnings` 확인.
- reverse proxy 사용 시 내부망 제한.

### R2. Java Adapter 미구현 상태에서 운영 착각

위험도: 높음

대응:

- 서버 프로젝트에 실제 Adapter 구현 클래스를 별도로 작성.
- 생성 실패 시 `failed` 상태와 `last_error`를 반드시 확인.
- `/dashboard/robot-spawn-queue/gui?status=failed&server_name=main` 운영 확인.

### R3. DB table 일부 미적용

위험도: 중간

대응:

- `/health/details`에서 `missing_tables` 확인.
- 누락 시 표시되는 `required_sql` 파일 적용.

### R4. MySQL 5.5 제약

위험도: 중간

대응:

- `JSON` column, generated column 사용 금지.
- `utf8mb4` 대신 기존 호환 기준 `utf8` 유지.
- `tests/test_mysql55_schema_compat.py` 유지.

### R5. Dashboard 복구 버튼 오남용

위험도: 낮음에서 중간

대응:

- 운영자는 `server_name`과 `limit`를 확인한 뒤 실행.
- GUI에서 server_name 필터를 먼저 적용한 뒤 복구 버튼을 사용.

## 반영 완료된 주요 개선

### C1. Spawn Queue Dashboard server_name 필터

목표:

- 여러 서버가 같은 AIA DB를 볼 때 server별 상태를 분리.

지원 API:

```http
GET /dashboard/robot-spawn-queue?server_name=main
GET /dashboard/robot-spawn-queue?status=failed&server_name=main
GET /dashboard/robot-spawn-queue/gui?server_name=main
GET /dashboard/robot-spawn-queue/gui?status=failed&server_name=main
```

## 다음 개선 우선순위

### P1. Adapter 구현 가이드 문서 보강

목표:

- L1J/L1J-KR 계열 서버에 붙일 때 어디에 연결해야 하는지 문서화.

포함 항목:

- 서버 시작 루틴 연결 위치
- IdFactory 연결
- character/robot table insert 위치
- World spawn 위치
- AI scheduler 등록 위치

### P2. CI 실패 대응 문서 추가

목표:

- GitHub Actions 실패 시 초보자도 어디를 봐야 하는지 알 수 있게 정리.

포함 항목:

- Python 실패
- MySQL 통합 테스트 실패
- Java compile 실패
- pip check 실패

### P3. DB bridge PostgreSQL 명시 DDL 분리

목표:

- 현재는 주력 대상이 MySQL 5.5이지만, PostgreSQL backend를 유지한다면 문자열 치환 대신 명시 DDL이 안전합니다.

### P4. 운영용 audit log

목표:

- 누가 spawn request를 만들었는지, 누가 retry/recover를 눌렀는지 기록.

## 현재 권장 운영 명령

AIA 실행:

```bash
python runners/server/run_local_aia.py
```

품질 게이트:

```bash
python runners/quality/run_quality_gates.py
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File runners/quality/run_quality_gates.ps1
```

상세 상태 확인:

```http
GET /health/details
GET /dashboard/robot-spawn-queue/gui?server_name=main
```

## 최종 판단

현재 구조는 “AIA가 직접 서버 DB를 마음대로 수정하지 않고, 서버가 poller/adapter로 통제하는 구조”이므로 방향은 좋습니다. 다음 개선의 핵심은 기능 추가보다 운영 안전성입니다.

우선순위는 다음입니다.

1. 인증/노출 안전성
2. Adapter 실서버 구현 가이드
3. CI 실패 대응 문서
4. 운영 audit log
