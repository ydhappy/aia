# MySQL DB Operations

## 운영 목적
MySQL 또는 MariaDB 기반 서버 환경에서 AIA DB bridge를 안정적으로 운용하기 위한 기준을 정리합니다.

## 필수 설정
- `DB_BRIDGE_BACKEND=mysql`
- `DB_BRIDGE_MYSQL_DSN=mysql+pymysql://user:password@host:3306/aia`

## 권장 대상
- 기존 MySQL 기반 게임 서버
- 서버 소스 최소화가 필요한 환경
- DB 중심 연동을 선호하는 운영 구조

## 권장 운영 원칙
- 상태는 최신값 중심 조회
- 이벤트/피드백은 append-only 운용
- decision/trace는 보존 주기 정책 수립
- 대량 운영 시 인덱스 최적화 필요

## 성능 권장
- `DB_BRIDGE_POLL_LIMIT` 조정
- `DB_BRIDGE_WRITE_BATCH_SIZE` 조정
- shard 단위 polling 분리
- trace compact mode 사용 권장

## 주의점
- 단일 MySQL 노드에 과도한 polling을 집중하지 않기
- 운영 환경에서는 slow query 및 index 점검 필수
