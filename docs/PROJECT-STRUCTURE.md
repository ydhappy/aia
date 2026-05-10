# 프로젝트 폴더 구조

AIA는 순수 코드, 서버 연동 계약 코드, 실행 코드를 분리합니다.

## 최상위 구조

```text
app/                 Python 애플리케이션 코드
sql/                 MySQL 5.5 호환 SQL
integration/java8/   게임서버에 붙일 Java 8 계약/클라이언트 코드
runners/             사람이 직접 실행하는 실행 코드
tests/               pytest 테스트
docs/                운영/연동 문서
```

예제/샘플 전용 폴더는 유지하지 않습니다.

## app 구조

```text
app/api/       FastAPI route
app/core/      설정, 보안, DB 연결, 공통 상수, live JSON loader
app/models/    Pydantic 모델
app/policies/  역할별 판단 정책
app/services/  서비스 로직
app/ui/        HTML UI 렌더러
app/graphs/    판단 그래프
app/utils/     검증기/유틸리티
```

## app/models 짧은 파일명

`models` 폴더 안에서는 파일명에 다시 `models`를 붙이지 않습니다.

```text
app/models/req.py     요청 모델
app/models/res.py     응답 모델
app/models/dash.py    Dashboard 모델
app/models/uni.py     통합 API 모델
app/models/auto.py    Automation 모델
app/models/batch.py   Batch 모델
```

삭제된 구파일명:

```text
app/models/request_models.py
app/models/response_models.py
app/models/dashboard_models.py
app/models/unified_api_models.py
app/models/automation_models.py
app/models/batch_models.py
```

## app/services 짧은 파일명

`services` 폴더 안에서는 파일명에 다시 `service`를 반복하지 않습니다.

```text
app/services/spawn.py       로봇 생성 요청 서비스
app/services/spawn_dash.py  Spawn Queue 대시보드 서비스
app/services/autonomy.py    자율운영 설정/프로필 서비스
```

삭제된 구파일명:

```text
app/services/robot_spawn_request_service.py
app/services/spawn_request_dashboard_service.py
app/services/robot_autonomy_baseline_service.py
```

## app/ui

```text
app/ui/spawn_queue.py  Spawn Queue GUI 렌더러
```

삭제된 구파일명:

```text
app/services/spawn_request_dashboard_renderer.py
```

## app/core

```text
app/core/names.py       테이블명, 상태명, SQL 파일명, 클래스 ID
app/core/live_json.py   운영 JSON 파일 실시간 reload helper
```

운영 JSON 파일은 `LiveJsonFile` 기준으로 파일 수정 시간이 바뀌면 다음 요청에서 다시 읽습니다.

대상 파일:

```text
app/config/robot_autonomy_defaults.json
app/config/aia_robot_top_profile.json
```

## Java 8 서버 연동 코드

```text
integration/java8/LocalAiaClient.java
integration/java8/AiaRobotSpawnRequest.java
integration/java8/AiaRobotSpawnAdapter.java
integration/java8/AiaRobotSpawnPoller.java
integration/java8/AiaDecisionParser.java
integration/java8/DbDecisionPoller.java
```

`integration/java8/`의 package는 `integration.java8`입니다. 이 폴더의 파일은 실제 게임서버에 복사해 붙이는 것을 기준으로 합니다.

## 실행 코드

```text
runners/server/      AIA 서버 실행
runners/setup/       로컬 설치/Windows 준비
runners/smoke/       HTTP smoke 테스트
runners/db/          DB seed/운영용 실행 스크립트
runners/quality/     품질 게이트 실행
```

## 실행 명령

AIA 실행:

```bash
python runners/server/run_local_aia.py
```

로컬 설치:

```bash
python runners/setup/bootstrap_local.py
```

Smoke 테스트:

```bash
python runners/smoke/ops_tick_smoke.py
python runners/smoke/robot_crud_smoke.py
```

Linux/GitHub Actions 품질 게이트:

```bash
python runners/quality/run_quality_gates.py
```

Windows 품질 게이트:

```powershell
powershell -ExecutionPolicy Bypass -File runners/quality/run_quality_gates.ps1
```

Java 컴파일 출력:

```text
build/java8-classes/
```

## 주요 테스트 파일

```text
tests/test_mods.py
tests/test_auto_live.py
tests/test_spawn_api.py
tests/test_spawn_dash.py
tests/test_spawn_ui.py
tests/test_mysql55.py
tests/test_mysql_spawn_queue_integration.py
```

## 원칙

- `app/`에는 실행용 main script를 두지 않습니다.
- `integration/java8/`에는 서버에 복사할 계약/클라이언트 코드만 둡니다.
- `runners/`에는 사람이 직접 실행하는 파일만 둡니다.
- 예제/샘플 전용 코드는 유지하지 않습니다.
- 반복 문자열은 `app/core/names.py`에 모읍니다.
- 화면 파일명은 `app/ui/`에서 짧고 목적 중심으로 둡니다.
- `models` 폴더 안에서는 `*_models.py`를 만들지 않습니다.
- `services` 폴더 안에서는 `*_service.py`를 새로 만들지 않습니다.
