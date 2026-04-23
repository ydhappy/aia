# MySQL DB Bridge

## 목적
기존 게임 서버가 MySQL 계열을 쓰는 경우 AIA와 가장 쉽게 연동할 수 있도록 MySQL DB bridge 구성을 제공합니다.

## 설정
- `DB_BRIDGE_BACKEND=mysql`
- `DB_BRIDGE_MYSQL_DSN=mysql+pymysql://root:root@localhost:3306/aia`

## 요구사항
- `PyMySQL`
- MySQL 또는 MariaDB

## 자동 생성 테이블
- `aia_robot_state`
- `aia_robot_event`
- `aia_robot_feedback`
- `aia_robot_decision`
- `aia_robot_trace_summary`

## 사용 API
- `GET /db-bridge/states`
- `GET /db-bridge/events`
- `GET /db-bridge/feedback`
- `POST /db-bridge/decision`
- `POST /db-bridge/trace`

## 권장 용도
- 기존 MySQL 기반 게임 서버
- 서버 소스 최소화가 중요한 운영 환경
- DB 중심 교환 구조

## 주의점
- 대규모 환경에서는 인덱스와 partitioning 검토가 필요합니다.
- 상태 테이블은 upsert 구조로 운영하는 것이 더 좋습니다.
- 서버 운영 테이블은 `robot`, `robot_clan`, `robot_setting`만 직접 관리하고, AIA 기록은 `aia_*` 접두사로 분리합니다.
