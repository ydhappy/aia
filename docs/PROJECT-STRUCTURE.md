# 프로젝트 폴더 구조

AIA는 순수 코드와 실행 코드를 분리합니다.

## 순수 코드 / 계약 코드

```text
app/                 Python 애플리케이션 코드
sql/                 MySQL 5.5 호환 SQL
integration/java8/   게임서버에 붙일 Java 8 계약/클라이언트 코드
tests/               pytest 테스트
```

## 실행 코드

```text
runners/server/      AIA 서버 실행
runners/setup/       로컬 설치/Windows 준비
runners/smoke/       HTTP smoke 테스트
runners/db/          DB seed/운영용 실행 스크립트
runners/quality/     품질 게이트 실행
```

## 예제 코드

```text
examples/java8/      Java 8 main 예제
```

## 실행 예시

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

Windows 품질 게이트:

```powershell
powershell -ExecutionPolicy Bypass -File runners/quality/run_quality_gates.ps1
```

## 원칙

- `app/`에는 실행용 main script를 두지 않습니다.
- `integration/java8/`에는 서버에 복사할 계약/클라이언트 코드만 둡니다.
- `examples/java8/`에는 실행 가능한 Java main 예제만 둡니다.
- `runners/`에는 사람이 직접 실행하는 파일만 둡니다.
