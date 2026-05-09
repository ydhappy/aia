# AIA 리팩토링 / 보강 체크리스트

전체 코드, DB, Java 연동, 스크립트, 테스트를 한 번에 크게 바꾸지 않고 파트별로 점검합니다.

## 진행 원칙

- 한 파트는 작은 범위로 제한한다.
- 서버 원본 DB 테이블은 직접 수정하지 않는다.
- MySQL 5.5 호환을 유지한다.
- Java 8 호환을 유지한다.
- 변경마다 테스트 또는 문서 근거를 남긴다.

## Part 1. 구조/설정/명백 오류 점검 - 완료

체크 결과:

- 라우트 등록 상태 확인.
- `/robot/spawn-requests`가 `/robot/{agent_id}`보다 앞에 있어 경로 충돌 없음.
- `.env.example`을 서버 연동 기본값으로 정리.
- `STATE_STORE_MODE=memory` 기본 적용.
- `ENABLE_API_KEY_AUTH=false` 기본 적용.
- MySQL 5.5 예시 DSN 반영.
- spawn request validation 보강.
- `level_min > level_max` 차단.
- 빈 `classes` 차단.
- 관련 테스트 보강.

주요 커밋:

- `chore: align env example with server integration defaults`
- `fix: validate robot spawn request ranges`
- `test: cover robot spawn request validation`

## Part 2. Robot CRUD / Spawn Request 안정화 - 완료

체크 결과:

- `/robot/{agent_id}`와 고정 경로 충돌 없음.
- spawn request 생성 응답에 `submitted`, `affected`, `duplicate_policy`, `required_table` 추가.
- MySQL 미사용 fallback 응답에 `required_table` 포함.
- class 값 정규화 보강.
- 중복 request 처리 정책을 응답에 명시.
- failed retry / stale claimed recovery 응답을 표준화.
- recovery 응답에 `action`, `server_name`, `limit`, `updated` 일관 적용.
- 관련 테스트 보강.

주요 커밋:

- `refactor: clarify spawn request creation response`
- `refactor: standardize spawn queue recovery responses`
- `test: assert standardized spawn queue recovery response`

## Part 3. DB / SQL 정합성 - 완료

체크 결과:

- MySQL 5.5용 bridge 자동 생성 DDL을 명시형 `MYSQL_BRIDGE_SCHEMA_SQL`로 분리.
- SQLite용 `TEXT NOT NULL DEFAULT ''` 변환 방식 제거.
- MySQL 5.5에서 깨질 수 있는 `TEXT/LONGTEXT DEFAULT` 방지.
- `ENGINE=InnoDB DEFAULT CHARSET=utf8` 유지.
- JSON column / generated column 미사용 테스트 추가.
- spawn request SQL도 MySQL 5.5 호환 테스트 추가.
- 품질 게이트에 `tests/test_mysql55_schema_compat.py` 추가.

주요 커밋:

- `fix: use explicit MySQL 5.5 bridge schema`
- `test: guard MySQL 5.5 schema compatibility`
- `test: add MySQL 5.5 schema compatibility gate`

## Part 4. Java 8 서버 연동부 - 완료

체크 결과:

- `LocalAiaClient`에 connect/read timeout 추가.
- `LocalAiaClient.healthCheck()` 추가.
- HTTP error stream이 null일 때 NPE가 나지 않도록 처리.
- HTTP 2xx가 아닌 응답은 body를 포함한 IOException으로 처리.
- 연결 종료 시 `disconnect()` 호출.
- `AiaRobotSpawnPoller`에 adapter null 방어 추가.
- `AiaRobotSpawnPoller`에 MySQL JDBC URL `useUnicode=true&characterEncoding=utf8` 자동 보정 추가.
- claim transaction 실패 시 rollback 처리 추가.
- 구형 서버 코드에 붙이기 쉽게 명시 close/rollback 구조로 보강.
- `DbDecisionPoller`에 JDBC URL charset 보정과 명시 close 추가.
- `AiaDecisionParser`의 escaped quote / nested object 처리 개선.
- Java 8 컴파일 게이트는 기존 `integration/java8/*.java` 전체 대상 유지.

주요 커밋:

- `refactor: harden Java8 local AIA HTTP client`
- `refactor: harden Java8 spawn poller JDBC handling`
- `refactor: harden Java8 DB decision poller`
- `refactor: improve Java8 decision parser escaping`

## Part 5. 스크립트 / 품질 게이트 - 완료

대상:

- `scripts/*.py`
- `scripts/*.ps1`
- `tests/*.py`

체크 결과:

- 원클릭 관련 잔여 검색 완료: 남은 참조 없음.
- `scripts/run_local_aia.py` 기본 포트를 문서/.env 기준인 `8000`으로 통일.
- `scripts/bootstrap_local.py`가 서버 연동 기본값을 훼손하지 않도록 수정.
- bootstrap 출력 문구를 서버 연동 기준으로 정리.
- `ops_tick_smoke.py`에 HTTP/비JSON/서버 미실행 오류 메시지 보강.
- `robot_crud_smoke.py`에 HTTP/비JSON/서버 미실행 오류 메시지 보강.
- 품질 게이트는 Python compile, 주요 API 테스트, MySQL 5.5 SQL 테스트, 전체 pytest, pip check, Java 8 compile 순서 유지.

주요 커밋:

- `fix: align local AIA runner default port`
- `fix: align bootstrap with server integration defaults`
- `refactor: improve ops tick smoke errors`
- `refactor: improve robot CRUD smoke errors`

## Part 6. GUI / Dashboard - 다음 진행 대상

대상:

- `app/api/routes_dashboard.py`
- `app/services/spawn_request_dashboard_service.py`
- `app/services/robot_ai_ops_service.py`

체크:

- spawn queue 필터/복구 UX
- HTML escape 누락 여부
- MySQL 미연결 fallback 화면
- 운영자가 즉시 볼 수 있는 상태 정보 보강

## Part 7. 최종 정리

체크:

- README / USAGE / API 문서와 실제 코드 일치
- 오래된 참조 검색
- 테스트 명령 정리
- 다음 개선 후보 목록화
