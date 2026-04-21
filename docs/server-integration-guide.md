# Server Integration Guide

## 목적
이 문서는 다양한 게임 서버가 AIA와 연동하는 방법을 설명합니다.
공용 배포를 전제로 하므로, 특정 서버 구조에 종속되지 않도록 작성합니다.

## 연동 방식 선택
### 1. 직접 API 연동
서버가 AIA REST API를 직접 호출합니다.

권장 대상:
- Java 서버
- C# 서버
- Go 게이트웨이
- Node.js 운영 서버

주요 엔드포인트:
- `POST /observe`
- `POST /decide`
- `POST /robot/profile`
- `POST /robot/event`
- `POST /robot/feedback`
- `POST /automation/task`
- `POST /api/v1/robot/sync`

### 2. DB 브리지 연동
서버는 상태/이벤트/피드백을 DB에 기록하고, AIA는 DB bridge 계층을 통해 읽고 씁니다.

권장 대상:
- 구형 서버
- 소스 수정 최소화가 필요한 서버
- 혼합형 서버 구조

### 3. 혼합 연동
- 상태와 이벤트는 DB 기록
- 결정은 REST API 호출
- 결과 피드백은 DB 또는 API로 반영

가장 현실적인 운영 방식입니다.

## 최소 연동 순서
1. 로봇 프로필 등록
2. 상태 observe 전송
3. 필요 시 decide 호출
4. 서버가 결과 검증 후 실행
5. 실행 결과 feedback 전송
6. 장기 루틴이 필요하면 automation task 등록

## 통합 연동 순서
한 번의 호출로 묶고 싶다면:
- `POST /api/v1/robot/sync`

이 엔드포인트는 다음을 한 번에 처리할 수 있습니다.
- profile
- events
- observe
- decide
- feedback
- automation task

## 서버 측 최소 책임
- 패킷 처리
- 실제 이동/공격/스킬 실행
- 최종 실행 검증
- 상태/이벤트/피드백 전송 또는 기록

## AIA 측 책임
- 판단
- 장기 자동화
- 학습
- 그룹 학습
- 맵별 적응
- 복구
- 관제
- 대규모 운영

## 권장 보안
공용 배포 기준에서는 반드시 다음을 권장합니다.
- 운영 API key 사용
- GitHub 토큰과 운영 키 분리
- 공개 인스턴스는 rate limiting 또는 게이트웨이 앞단 사용
- LLM 서버는 공개 노출보다 내부망 분리 권장

## 권장 배포 구조
- Game Server
- AIA
- Redis
- Self-Hosted LLM
- Optional DB bridge

## 연동 성공 기준
다음이 되면 연동이 성공한 것입니다.
- 로봇 상태가 정상 observe 됨
- decide 결과가 서버 행동 실행기로 연결됨
- invalid action fallback 동작함
- feedback가 누적됨
- automation task가 장기 루프를 생성함
- recovery와 dashboard API가 운영에 사용됨
