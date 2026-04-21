# Beginner Start Here

## 목표
초보자도 AIA를 처음부터 연동하고 실행할 수 있게 순서를 가장 단순하게 정리한 문서입니다.

## 1. 준비물
- Python 3.11 이상
- 게임서버 (예: Java 8)
- 선택: MySQL/MariaDB 또는 PostgreSQL

## 2. 저장소 받기
```bash
git clone <repo-url>
cd aia
```

## 3. 가장 쉬운 시작
가장 안전한 시작은 아래 한 줄입니다.

```bash
python one_click_start.py
```

이 스크립트가 하는 일:
- 가상환경 생성
- pip 업그레이드
- requirements 설치
- `.env.example`를 `.env`로 복사
- runtime 폴더 생성
- 안전 기본값 적용
  - `STATE_STORE_MODE=memory`
  - `DB_BRIDGE_BACKEND=sqlite`
- AIA 로컬 실행

즉, Redis/MySQL/PostgreSQL 없이도 먼저 AIA 자체는 바로 띄울 수 있습니다.

## 4. DB를 같이 쓰려면
MySQL/MariaDB 기준으로 먼저 SQL을 넣습니다.

```bash
mysql -u root -p your_database < sql/aia_robot_schema.sql
```

그 다음 `.env`에서 다음을 확인합니다.
- `DB_BRIDGE_BACKEND=mysql`
- `DB_BRIDGE_MYSQL_DSN=mysql+pymysql://user:password@127.0.0.1:3306/your_database`

## 5. 게임서버와 연동
권장 방식은 DB + 로컬 HTTP 혼합형입니다.

- 상태/이벤트/피드백/장기 이력: DB
- 즉시 전투 판단: `127.0.0.1:8000` 로컬 HTTP

Java 8 연동 파일:
- `integration/java8/LocalAiaClient.java`
- `integration/java8/DbDecisionPoller.java`
- `integration/java8/RobotStateExtractor.java`
- `integration/java8/RobotActionExecutor.java`
- `integration/java8/RobotStateWriter.java`
- `integration/java8/RobotEventWriter.java`
- `integration/java8/RobotFeedbackWriter.java`

## 6. 확인할 API
- `GET /health`
- `POST /decide`
- `POST /api/v1/robot/sync`
- `GET /goal/{agent_id}`
- `GET /growth/{agent_id}`

## 7. 초보자 권장 순서
1. `python one_click_start.py`
2. 브라우저나 API 도구로 `/health` 확인
3. DB를 쓸 경우 `sql/aia_robot_schema.sql` 적용
4. Java 8 서버에서 상태/피드백 기록 추가
5. 즉시 판단은 로컬 HTTP로 연결
