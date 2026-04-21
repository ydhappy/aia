# Quick Start for Public Users

## 1. 준비
필요한 것:
- AIA 주소
- 운영 API key
- 자신의 게임 서버 또는 테스트 브리지

## 2. 가장 쉬운 연동
가장 쉬운 방법은 통합 API를 쓰는 것입니다.
- `POST /api/v1/robot/sync`

이 API로 다음을 묶어서 보낼 수 있습니다.
- profile
- events
- observe
- decide
- feedback
- automation task

## 3. 최소 시작 흐름
1. 로봇 프로필 생성
2. 현재 상태 observe 전송
3. decide 결과 받기
4. 서버에서 검증 후 실행
5. 결과를 feedback로 다시 보내기

## 4. 장기 자동화
장기 작업이 필요하면 다음 API를 사용합니다.
- `POST /automation/task`
- `GET /automation/{agent_id}/next-step`

## 5. 운영 확인
- `GET /goal/{agent_id}`
- `GET /robot/{agent_id}/trace`
- `GET /robot/{agent_id}/learning`

## 6. 중요한 주의점
- AIA는 판단/자동화 계층입니다.
- 실제 실행 권한은 항상 게임 서버가 가져야 합니다.
- 공용 배포 환경에서는 관리자 API를 일반 사용자에게 열지 않는 것이 좋습니다.
