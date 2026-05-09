# AIA 리팩토링 / 보강 체크리스트

전체 코드, DB, Java 연동, 스크립트, 테스트를 한 번에 크게 바꾸지 않고 파트별로 점검합니다.

## 진행 원칙

- 한 파트는 작은 범위로 제한한다.
- 서버 원본 DB 테이블은 직접 수정하지 않는다.
- MySQL 5.5 호환을 유지한다.
- Java 8 호환을 유지한다.
- 변경마다 테스트 또는 문서 근거를 남긴다.

## Part 1. 구조/설정/명백 오류 점검

대상:

- `app/main.py`
- `app/api/*.py`
- `app/core/*.py`
- `app/services/store_factory.py`
- `.env.example`
- `requirements.txt`

체크:

- 라우트 등록 누락 여부
- import 순환 가능성
- API 경로 충돌 여부
- 설정 기본값과 문서 불일치 여부
- 테스트에서 깨질 수 있는 기본 상태 확인

## Part 2. Robot CRUD / Spawn Request 안정화

대상:

- `app/api/routes_knowledge.py`
- `app/models/request_models.py`
- `app/models/response_models.py`
- `app/services/robot_spawn_request_service.py`
- `app/services/spawn_request_dashboard_service.py`

체크:

- `/robot/{agent_id}`와 고정 경로 충돌 여부
- 요청 validation 강화
- MySQL 미사용 환경 fallback
- 중복 request 처리 정책
- failed/recover 처리 안전성

## Part 3. DB / SQL 정합성

대상:

- `sql/aia_robot_schema.sql`
- `sql/aia_robot_spawn_request_mysql55.sql`
- `app/services/db_bridge_service.py`

체크:

- MySQL 5.5 비호환 문법 제거
- charset `utf8` 유지
- JSON column/generation 미사용 확인
- index/unique key 중복 확인
- AIA-owned table과 server-owned table 경계 명확화

## Part 4. Java 8 서버 연동부

대상:

- `integration/java8/*.java`

체크:

- Java 8 문법만 사용
- try-with-resources 사용 가능 범위 확인
- PATCH fallback 안정성
- JDBC/MySQL 5.5 호환
- Adapter 예제와 실제 서버 연결 지점 명확화

## Part 5. 스크립트 / 품질 게이트

대상:

- `scripts/*.py`
- `scripts/*.ps1`
- `tests/*.py`

체크:

- 원클릭 관련 잔여 제거
- Windows/Linux 실행 명령 정합성
- smoke script API 경로 정합성
- pytest coverage 보강
- 품질 게이트 실패 메시지 개선

## Part 6. GUI / Dashboard

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
