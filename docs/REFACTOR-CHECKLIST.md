# AIA 리팩토링 / 보강 체크리스트

전체 코드, DB, Java 연동, 실행 코드, 테스트를 한 번에 크게 바꾸지 않고 파트별로 점검했습니다.

## 진행 원칙

- 한 파트는 작은 범위로 제한한다.
- 서버 원본 DB 테이블은 직접 수정하지 않는다.
- MySQL 5.5 호환을 유지한다.
- Java 8 호환을 유지한다.
- 순수 코드와 실행 코드를 분리한다.
- 변경마다 테스트 또는 문서 근거를 남긴다.

## Part 1. 구조/설정/명백 오류 점검 - 완료

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

## Part 2. Robot CRUD / Spawn Request 안정화 - 완료

- spawn request 생성 응답에 `submitted`, `affected`, `duplicate_policy`, `required_table` 추가.
- MySQL 미사용 fallback 응답에 `required_table` 포함.
- class 값 정규화 보강.
- 중복 request 처리 정책을 응답에 명시.
- failed retry / stale claimed recovery 응답을 표준화.
- recovery 응답에 `action`, `server_name`, `limit`, `updated` 일관 적용.
- 관련 테스트 보강.

## Part 3. DB / SQL 정합성 - 완료

- MySQL 5.5용 bridge 자동 생성 DDL을 명시형 `MYSQL_BRIDGE_SCHEMA_SQL`로 분리.
- SQLite용 `TEXT NOT NULL DEFAULT ''` 변환 방식 제거.
- MySQL 5.5에서 깨질 수 있는 `TEXT/LONGTEXT DEFAULT` 방지.
- `ENGINE=InnoDB DEFAULT CHARSET=utf8` 유지.
- JSON column / generated column 미사용 테스트 추가.
- spawn request SQL도 MySQL 5.5 호환 테스트 추가.
- 품질 게이트에 `tests/test_mysql55_schema_compat.py` 추가.

## Part 4. Java 8 서버 연동부 - 완료

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

## Part 5. 실행 코드 / 품질 게이트 - 완료

- 원클릭 관련 잔여 검색 완료: 남은 참조 없음.
- 실행 코드를 `runners/` 아래로 분리.
- 서버 실행: `runners/server/run_local_aia.py`.
- 로컬 준비: `runners/setup/bootstrap_local.py`.
- Smoke 테스트: `runners/smoke/ops_tick_smoke.py`, `runners/smoke/robot_crud_smoke.py`.
- DB seed 실행: `runners/db/seed_robot_spawn_requests_mysql55.py`.
- 품질 게이트: `runners/quality/run_quality_gates.ps1`.
- 오래된 `scripts/` 실행 파일 삭제.
- stale `auto_connect_run.py` 삭제.
- 품질 게이트는 Python compile, 주요 API 테스트, MySQL 5.5 SQL 테스트, 전체 pytest, pip check, Java 8 compile 순서 유지.

## Part 6. GUI / Dashboard - 완료

- Spawn Queue JSON 응답에 `total`, `needs_attention`, `operator_hint` 추가.
- DB backend가 MySQL이 아닐 때 운영자 조치 문구 표시.
- MySQL 연결/권한/테이블 오류 시 조치 문구 표시.
- 상태 카드가 `pending/claimed/done/failed` 네 가지를 항상 표시하도록 개선.
- GUI 상단에 정상/확인 필요 배너 추가.
- 최근 요청 테이블에 `request_id`, `priority`, `created_at` 표시 추가.
- failed retry / claimed recovery 버튼을 GUI에 추가.
- form body 방식 대신 query API에 맞춘 JavaScript `fetch()` 호출로 수정.
- HTML 출력은 기존 `escape()` 기반 유지.
- GUI 테스트에 새 필드와 버튼 동작 문구 검증 추가.

## Part 7. 최종 정리 - 완료

- 원클릭/Quickstart/18000포트/sqlite 강제 참조 검색 완료: 남은 참조 없음.
- README를 최종 API/테스트/유지 문서 기준으로 정리.
- `docs/USAGE.md`를 최종 Dashboard/테스트 기준으로 정리.
- `docs/API.md`에 spawn request 응답 필드와 queue 복구 query parameter 반영.
- `docs/PROJECT-STRUCTURE.md` 추가.
- 유지 문서 목록 확정.

## 현재 폴더 구조

```text
app/                 순수 Python 애플리케이션 코드
sql/                 MySQL 5.5 호환 SQL
integration/java8/   게임서버에 붙일 Java 8 계약/클라이언트 코드
examples/java8/      Java 8 실행 예제
runners/             사람이 직접 실행하는 실행 코드
tests/               pytest 테스트
```

## 유지 문서

```text
README.md
docs/USAGE.md
docs/SERVER-INTEGRATION.md
docs/API.md
docs/PROJECT-STRUCTURE.md
docs/REFACTOR-CHECKLIST.md
```

## 권장 테스트

```bash
pytest tests/test_robot_crud_api.py
pytest tests/test_robot_spawn_request_api.py
pytest tests/test_spawn_request_dashboard.py
pytest tests/test_mysql55_schema_compat.py
```

Windows 전체 게이트:

```powershell
powershell -ExecutionPolicy Bypass -File runners/quality/run_quality_gates.ps1
```

## 다음 개선 후보

- 실제 L1J 계열 서버 클래스명 기준 `MyServerRobotAdapter` 샘플 추가.
- Spawn Queue GUI에서 서버명 선택/최근 실패만 보기 추가.
- ops-tick Java 예제에 실제 이동/공격 실행 전 검증 샘플 추가.
- MySQL 연결 성공 여부를 `/health` 확장 항목으로 노출.
- GitHub Actions 또는 별도 CI에서 Python/Java 품질 게이트 자동화.
