# Runtime Language Strategy

## 핵심 판단
AIA 운영 코어는 현재 Python 기반이 가장 완성도가 높습니다.
하지만 게임 서버와 운영 주변 계층은 Python만 사용할 필요가 없습니다.

## 권장 구조
- AIA core: Python
- Game Server: 기존 언어 유지
- Gateway / UI / tools: 목적에 따라 별도 언어 사용

## 서버 언어별 전략
### Java
- L1J 계열 서버와 가장 자연스럽게 연결
- REST 또는 DB bridge 권장

### C++
- 구형 서버 코어 유지
- 최소 훅 + DB bridge 또는 별도 adapter 권장

### C#
- 운영도구, 매니저, 툴링 계층에 적합

### Go
- 대규모 shard gateway, 고성능 orchestration에 적합

### Node.js / TypeScript
- 관리자 UI, 웹 대시보드, 게이트웨이 계층에 적합

## 최종 운영 판단
- AIA 코어를 다른 언어로 옮기는 것보다
- 기존 서버 언어를 유지하고 AIA를 외부 운영 두뇌로 붙이는 것이 완성도와 비용 측면에서 가장 유리합니다.
