# Python + Java + Script Only Strategy

## 결론
DLL/EXE를 전면에 두지 않고도, 현재 AIA는 Python + Java 8 + script 중심으로 충분히 운영 가능합니다.

## 권장 구성
- Game Server: Java 8
- AIA Core: Python
- Local execution helpers: Python scripts
- Optional DB bridge: MySQL/PostgreSQL/SQLite

## 포함 파일
- `integration/java8/LocalAiaClient.java`
- `integration/java8/DbDecisionPoller.java`
- `scripts/run_local_aia.py`
- `scripts/run_scheduler_cycle.py`

## 권장 운영 방식
- 같은 서버 내 분리 실행
- Game server는 127.0.0.1 로컬 AIA를 호출
- 장기 운영 상태는 DB와 scheduler script로 관리
- 즉시 판단은 HTTP, 운영 이력은 DB 중심

## 목적
- Java 8 서버 유지
- Python AIA 활용
- DLL/EXE 의존 최소화
- 운영 자동화는 script로 보완
