# 프로젝트 폴더 구조

AIA는 순수 코드와 실행 코드를 분리합니다.

## 순수 코드 / 계약 코드

```text
app/                 Python 애플리케이션 코드
app/core/            설정, 보안, DB 연결, 공통 명칭 상수
app/services/        서비스 로직. 새 코드는 짧은 모듈명을 우선 사용
app/ui/              짧은 UI 렌더러
sql/                 MySQL 5.5 호환 SQL
integration/java8/   게임서버에 붙일 Java 8 계약/클라이언트 코드
tests/               pytest 테스트
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

## 짧은 명칭 기준

```text
app/core/names.py       테이블명, 상태명, SQL 파일명, 클래스 ID
app/core/live_json.py   운영 JSON 파일 실시간 reload helper
app/services/spawn.py       로봇 생성 요청 서비스 공식 경로
app/services/spawn_dash.py  Spawn Queue 대시보드 서비스 공식 경로
app/services/autonomy.py    로봇 자율운영 설정 서비스 공식 경로
app/ui/spawn_queue.py       Spawn Queue GUI 렌더러
```

운영 JSON 파일은 `LiveJsonFile` 기준으로 파일 수정 시간이 바뀌면 다음 요청에서 다시 읽는 구조를 사용합니다.

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

## 원칙

- `app/`에는 실행용 main script를 두지 않습니다.
- `integration/java8/`에는 서버에 복사할 계약/클라이언트 코드만 둡니다.
- `runners/`에는 사람이 직접 실행하는 파일만 둡니다.
- 예제/샘플 전용 코드는 유지하지 않습니다.
- 반복 문자열은 `app/core/names.py`에 모읍니다.
- 화면 파일명은 짧고 목적 중심으로 둡니다.
- 새 코드에서는 `robot_spawn_request_service.py`, `spawn_request_dashboard_service.py`, `robot_autonomy_baseline_service.py` 같은 긴 경로 대신 `spawn.py`, `spawn_dash.py`, `autonomy.py`를 사용합니다.
