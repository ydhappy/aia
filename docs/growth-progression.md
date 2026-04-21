# Growth Progression

## 목적
로봇이 단순 행동 추천을 넘어서 경험 축적과 숙련도 기반 성장 상태를 가지도록 하기 위한 구조를 설명합니다.

## 현재 포함 요소
- overall growth score
- action score
- role mastery
- map mastery
- failure tags
- stage classification

## 성장 단계
- novice
- stable
- optimized
- expert

## 갱신 시점
- `POST /robot/feedback`
- feedback 입력 시 learning과 함께 growth도 갱신됨

## 조회 API
- `GET /growth/{agent_id}`

## 운영 목적
- 어떤 로봇이 아직 초보 단계인지 확인
- 어떤 역할/맵에서 숙련도가 높은지 확인
- 실패 패턴을 보고 정책 보정 포인트를 찾기
