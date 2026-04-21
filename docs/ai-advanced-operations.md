# Advanced AI Operations

## 포함된 고도화 축
- growth progression
- role/map mastery
- failure analysis
- anomaly detection
- meta policy selection
- growth-aware tactical policy
- fully integrated automation planning

## 현재 흐름
1. observe/state/profile/event 입력
2. learning / growth state 조회
3. anomaly detection 수행
4. meta policy 선택
5. policy engine가 growth stage와 meta policy를 반영
6. automation은 goal/fsm/economy/npc를 통합한 next-step 생성
7. feedback 입력 시 learning + growth 동시 갱신

## 운영 목적
- 초보 단계 로봇은 보수적으로 운용
- 성장한 로봇은 효율적으로 운용
- 이상행동이 탐지되면 안정성 우선 전략으로 전환
- 복구, 관제, scale 운영과 함께 전체 안정성 유지

## 핵심 API
- `POST /observe`
- `POST /decide`
- `POST /robot/feedback`
- `GET /growth/{agent_id}`
- `GET /goal/{agent_id}`
- `GET /robot/{agent_id}/trace`
- `POST /automation/task`
- `GET /automation/{agent_id}/next-step`
