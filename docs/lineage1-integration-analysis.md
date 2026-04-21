# Lineage 1 Open Source Server Integration Analysis

## 기준 코드베이스
실무 기준에서는 l1j-en/classic 계열을 기준점으로 보는 것이 가장 현실적입니다.

## 연동 전 상태
일반적인 L1J 계열 서버는 다음이 강점입니다.
- 맵/캐릭터/전투/아이템/스폰/AI 기본 구조 보유
- 오래된 운영 노하우와 안정성 자산 존재
- Java 기반이라 AIA REST 연동이 용이

일반적인 약점은 다음과 같습니다.
- 봇 운영이 대부분 단발성 규칙 위주
- 장기 목표 기반 자동화 부족
- 학습/피드백 루프 부재
- 대규모 봇 관제 API 부재
- 자동 복구/관제 분리 미흡

## AIA 연동 후 기대 완성도
### 1. 전술 판단 완성도
- 기존 서버 전투/이동/타겟팅 구조 위에 AIA 정책 엔진을 얹으면 높은 편
- 서버는 최종 실행/검증만 담당하고, AIA는 판단을 담당
- 완성도: 높음

### 2. 장기 자동화 완성도
- farm/patrol/support/return-and-resume 같은 장기 루틴 추가 가능
- 기존 L1J가 약한 장기 목표 계층을 보완
- 완성도: 높음

### 3. 학습 적응 완성도
- 행동 결과 피드백을 받아 preferred/avoid action을 누적
- 맵별/그룹별 적응 가능
- 다만 완전한 강화학습 학습기 수준은 아님
- 완성도: 중상

### 4. 운영/관제 완성도
- unified API, scale API, dashboard, admin recovery, ops scheduler 추가로 운영성이 크게 개선됨
- 기존 L1J 단독 대비 큰 폭 상승
- 완성도: 매우 높음

### 5. 대규모 봇 운영 완성도
- shard batching, bulk recovery, Redis 공유 상태, self-hosted LLM 분리 운영으로 확장 가능
- 10 ~ 10000 단위 운영 구조 설계 가능
- 실제 성능은 서버/DB/네트워크 튜닝에 좌우
- 완성도: 높음

## 구체적 연동 시 필요한 실제 작업
### 서버 쪽
- observe payload 생성
- decide 결과를 기존 move/attack/skill 실행기로 연결
- invalid action fallback 구현
- action whitelist 검증 구현
- feedback 전송 지점 구현
- automation task 등록/갱신 지점 구현

### AIA 쪽
- role/profile/event 스키마 확정
- map override 정책 확정
- world profile 구성
- Redis 운영 여부 확정
- self-hosted LLM 사용 범위 제한

## 완성도 평가표
- 전투/이동/기본 게임 로직: L1J 강점
- 장기 자동화: AIA로 크게 보강
- 학습 적응: AIA로 중상 수준 확보
- 운영 관제: AIA로 매우 크게 보강
- 자동 복구: AIA로 실무 수준 확보
- 완전 무인 코드 자기수정: 미포함

## 최종 판단
리니지1 오픈소스 서버에 AIA를 연동하면,
단순 서버 에뮬레이터에서 끝나는 것이 아니라
- 전술 판단
- 장기 자동화
- 학습 적응
- 대규모 운영
- 복구/관제
를 가진 운영형 로봇 플랫폼으로 확장됩니다.

실무 감각으로 보면 완성도는 다음 정도로 볼 수 있습니다.
- 기본 서버 기능: L1J가 담당
- 운영형 로봇 플랫폼 기능: AIA가 담당
- 두 개를 합치면 전체 완성도는 중상~높음 수준

단, 최종 품질은 서버 내부 연동 지점(move/attack/skill/feedback/task hook)을 얼마나 잘 심느냐에 크게 좌우됩니다.
