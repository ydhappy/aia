# AIA 리팩토링 / 보강 체크리스트

이 문서는 AIA의 코드, DB, Java 연동, 실행 코드, 테스트, 문서 정리 결과를 최신 상태로 요약합니다.

## 진행 원칙

- 서버 원본 DB 테이블은 AIA가 직접 수정하지 않는다.
- MySQL 5.5 호환을 유지한다.
- Java 8 호환을 유지한다.
- 순수 코드와 실행 코드를 분리한다.
- 예제/샘플 전용 코드는 유지하지 않는다.
- 폴더명과 파일명에서 같은 의미를 반복하지 않는다.
- 변경마다 테스트 또는 문서 근거를 남긴다.

## Part 1. 구조/설정/명백 오류 점검 - 완료

- 라우트 등록 상태 확인.
- `/robot/spawn-requests`와 `/robot/{agent_id}` 경로 충돌 방지 확인.
- `.env.example`을 local 기본값으로 정리.
- `APP_ENV=local` 기본 적용.
- `STATE_STORE_MODE=memory` 기본 적용.
- MySQL 5.5 예시 DSN 반영.
- `/health/details`에 보안 경고 추가.
- `security.warnings`에 API key/auth/public bind 상태 표시.

## Part 2. Robot CRUD / Spawn Request 안정화 - 완료

- spawn request 생성 응답에 `submitted`, `affected`, `duplicate_policy`, `required_table` 추가.
- MySQL 미사용 fallback 응답에 `required_table` 포함.
- class 값 정규화 보강.
- 중복 request 처리 정책을 응답에 명시.
- failed retry / stale claimed recovery 응답을 표준화.
- 복구 API는 `server_name` 단위로 동작.
- Spawn Queue Dashboard에 `server_name` 필터 추가.

## Part 3. DB / SQL 정합성 - 완료

- MySQL 5.5용 bridge DDL을 명시형 `MYSQL_BRIDGE_SCHEMA_SQL`로 분리.
- SQLite용 `TEXT NOT NULL DEFAULT ''` 변환 방식 제거.
- MySQL 5.5에서 깨질 수 있는 `TEXT/LONGTEXT DEFAULT` 방지.
- `ENGINE=InnoDB DEFAULT CHARSET=utf8` 유지.
- JSON column / generated column 미사용 테스트 추가.
- spawn request SQL도 MySQL 5.5 호환 테스트 추가.
- `/health/details`에서 필수 테이블 존재 여부와 required SQL 파일 표시.

## Part 4. Java 8 서버 연동부 - 완료

- `LocalAiaClient`에 connect/read timeout 추가.
- `LocalAiaClient.healthCheck()` 추가.
- HTTP error stream null 방어.
- HTTP 2xx가 아닌 응답은 body를 포함한 IOException으로 처리.
- 연결 종료 시 `disconnect()` 호출.
- `AiaRobotSpawnPoller`에 adapter null 방어 추가.
- MySQL JDBC URL `useUnicode=true&characterEncoding=utf8` 자동 보정 추가.
- claim transaction 실패 시 rollback 처리 추가.
- `DbDecisionPoller`에 JDBC URL charset 보정과 명시 close 추가.
- `AiaDecisionParser`의 escaped quote / nested object 처리 개선.

## Part 5. 실행 코드 / 품질 게이트 - 완료

- 원클릭 관련 잔여 참조 제거.
- 실행 코드를 `runners/` 아래로 분리.
- 서버 실행: `runners/server/run_local_aia.py`.
- 로컬 준비: `runners/setup/bootstrap_local.py`.
- Smoke 테스트: `runners/smoke/ops_tick_smoke.py`, `runners/smoke/robot_crud_smoke.py`.
- DB seed 실행: `runners/db/seed_robot_spawn_requests_mysql55.py`.
- 품질 게이트: `runners/quality/run_quality_gates.py`, `runners/quality/run_quality_gates.ps1`.
- 오래된 `scripts/` 실행 파일 삭제.
- 품질 게이트는 Python compile, 주요 API 테스트, MySQL 5.5 SQL 테스트, 전체 pytest, pip check, Java 8 compile 순서 유지.

## Part 6. GUI / Dashboard - 완료

- Spawn Queue JSON 응답에 `total`, `needs_attention`, `operator_hint` 추가.
- DB backend가 MySQL이 아닐 때 운영자 조치 문구 표시.
- 상태 카드가 `pending/claimed/done/failed` 네 가지를 항상 표시하도록 개선.
- GUI 상단에 정상/확인 필요 배너 추가.
- 최근 요청 테이블에 `request_id`, `priority`, `created_at` 표시 추가.
- failed retry / claimed recovery 버튼 추가.
- `server_name` 필터와 전체 서버 보기 추가.
- HTML 출력은 `escape()` 기반 유지.
- GUI 테스트에 필드, 버튼, server filter 검증 추가.

## Part 7. 명칭/파일명 단순화 - 완료

### 모델 파일

현재 공식 파일:

```text
app/models/req.py
app/models/res.py
app/models/dash.py
app/models/uni.py
app/models/auto.py
app/models/batch.py
```

삭제된 구파일:

```text
app/models/request_models.py
app/models/response_models.py
app/models/dashboard_models.py
app/models/unified_api_models.py
app/models/automation_models.py
app/models/batch_models.py
```

### 서비스 파일

현재 공식 파일:

```text
app/services/spawn.py
app/services/spawn_dash.py
app/services/autonomy.py
```

삭제된 구파일:

```text
app/services/robot_spawn_request_service.py
app/services/spawn_request_dashboard_service.py
app/services/robot_autonomy_baseline_service.py
```

### UI 파일

현재 공식 파일:

```text
app/ui/spawn_queue.py
```

삭제된 구파일:

```text
app/services/spawn_request_dashboard_renderer.py
```

## Part 8. 실시간 운영 설정 반영 - 완료

- `app/core/live_json.py` 추가.
- `LiveJsonFile`은 파일 mtime 변경 시 다음 요청에서 자동 reload.
- `app/services/autonomy.py`에 실제 적용.
- 대상 파일:

```text
app/config/robot_autonomy_defaults.json
app/config/aia_robot_top_profile.json
```

- `/dashboard/robot-autonomy-baseline` 응답에 `live_reload` 정보 노출.
- `tests/test_auto_live.py`로 검증.

## 현재 폴더 구조

```text
app/                 Python 애플리케이션 코드
app/core/            설정, 보안, DB 연결, 공통 명칭 상수, live JSON
app/models/          req/res/dash/uni/auto/batch
app/services/        spawn/spawn_dash/autonomy 등 서비스 로직
app/ui/              HTML UI 렌더러
sql/                 MySQL 5.5 호환 SQL
integration/java8/   게임서버에 붙일 Java 8 계약/클라이언트 코드
runners/             사람이 직접 실행하는 실행 코드
tests/               pytest 테스트
docs/                운영/연동 문서
```

## 유지 문서

```text
README.md
docs/USAGE.md
docs/SERVER-INTEGRATION.md
docs/API.md
docs/PROJECT-STRUCTURE.md
docs/REFACTOR-CHECKLIST.md
docs/THIRD-PARTY-REVIEW.md
```

## 권장 테스트

전체 품질 게이트:

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

선택형 MySQL 통합 테스트:

```bash
AIA_TEST_MYSQL_DSN=mysql+pymysql://root:root@127.0.0.1:3306/aia_ci \
python -m pytest tests/test_mysql_spawn_queue_integration.py
```

Windows 전체 게이트:

```powershell
powershell -ExecutionPolicy Bypass -File runners/quality/run_quality_gates.ps1
```

## 다음 개선 후보

- 실제 L1J 계열 서버 클래스명 기준 Adapter 구현 가이드 추가.
- CI 실패 대응 문서 추가.
- 운영 audit log 추가.
- PostgreSQL backend를 유지할 경우 명시 DDL 분리.
