# Public Deployment Guide

## 목표
AIA를 공용 배포하여 여러 사용자가 사용할 수 있게 할 때 필요한 기준을 정리합니다.

## 기본 원칙
- 공개 사용은 가능하지만, 무제한 공개보다 인증과 운영 게이트를 두는 것이 안전합니다.
- Game Server 실행 권한은 각 사용자의 서버가 보유하고, AIA는 판단/자동화/운영 기능을 제공합니다.
- self-hosted LLM은 공개 웹에 직접 노출하지 않는 것을 권장합니다.

## 필수 권장 사항
### 인증
- `ENABLE_API_KEY_AUTH=true`
- 운영 통신용 API key 적용
- 가능하면 사용자/서버별 키 분리 권장

### 운영 분리
- 공개 API 계층
- 내부 Redis
- 내부 self-hosted LLM
- 내부 DB bridge

### 과부하 방지
- scale/batch 사용 권장
- 대규모 사용자는 shard 분리 권장
- dashboard와 ops API는 관리자 키로 제한 권장

## 공용 배포 시 노출 권장 API
외부 사용자가 직접 쓰기 쉬운 API는 다음입니다.
- `/api/v1/robot/sync`
- `/observe`
- `/decide`
- `/automation/task`

## 관리자 전용 권장 API
다음은 관리자 전용으로 두는 것을 권장합니다.
- `/admin/*`
- `/dashboard/*`
- `/scale/*`
- `/db-bridge/*`
- `/ops/*`

## 공용 배포 주의점
- 공개 인스턴스는 악의적 대량 호출에 취약할 수 있음
- 서버 실행 결과는 항상 각 게임 서버가 최종 검증해야 함
- 자동 복구는 보수적으로 동작해야 함
- 공용 환경에서는 LLM 호출 빈도를 강하게 제한하는 것이 좋음

## 권장 공개 형태
### 소규모 공개
- 단일 AIA 인스턴스
- Redis 1대
- 운영 키 1개 이상

### 중규모 공개
- AIA 다중 인스턴스
- Redis 공유
- self-hosted LLM 분리
- shard 기반 운영

### 대규모 공개
- 공개 API gateway
- 내부 AIA cluster
- Redis
- 내부 self-hosted LLM cluster
- 관리자 전용 관제 계층
