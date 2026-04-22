# Self-Hosted LLM Architecture

## 목표
외부 API형 LLM이 아니라 **자체 운영 LLM 서버**를 별도 추론 노드로 띄우고, AIA가 그 서버에 연결되도록 구성합니다.

## 권장 구조
- Game Server
- AIA Bridge Server
- Self-Hosted LLM Inference Server
- Optional Redis

## 핵심 원칙
- 게임 서버는 가볍게 유지
- 모델 가중치는 게임 서버가 아니라 별도 추론 서버에 둠
- AIA는 규칙 엔진, 에이전트 그래프, 액션 검증만 담당
- LLM은 OpenAI 호환 API 또는 llama.cpp/Ollama 형태로 별도 노드에서 제공

## 권장 배치
### 1. 같은 내부망 분리형
- game-server-01
- aia-bridge-01
- llm-inference-01

### 2. 월드별 분리형
- world-1 -> aia-1 -> llm-1
- world-2 -> aia-2 -> llm-2

### 3. 공유 추론 서버형
- 여러 게임 서버가 하나의 AIA 또는 여러 AIA를 사용
- 여러 AIA가 하나의 self-hosted LLM inference cluster를 공유

## 설정 방향
- `LLM_BACKEND=self_hosted`
- `LLM_PROVIDER=openai_compatible`
- `LLM_BASE_URL=http://your-llm-node:8001`
- `LLM_MODEL=your-local-model-name`
- `LLM_API_KEY=` 선택

## 오픈소스 에이전트 흡수 원칙

AIA는 외부 프레임워크 코드를 기본으로 vendoring하지 않습니다. 대신 `/ops/open-agent-providers`에서 지원 후보와 흡수 계획을 노출하고, 외부 런타임은 sidecar로 연결합니다.

권장 흡수 순서:
- 1순위: AIA Native Autonomy Core는 항상 최종 정책 계층으로 유지합니다.
- 2순위: Ollama/OpenAI-compatible 런타임은 LLM 추론 sidecar로 연결합니다.
- 3순위: LangGraph 또는 Microsoft Agent Framework는 장기 운영/멀티에이전트 sidecar로 연결합니다.
- 4순위: CrewAI는 역할 기반 워크플로 sidecar로 선택 적용합니다.
- 참고: AutoGen은 maintenance-mode로 확인되므로 신규 핵심 의존성으로 삼지 않고 패턴/마이그레이션 참고용으로 둡니다.

안전 규칙:
- 외부 에이전트는 게임 액션을 직접 실행하지 않습니다.
- 외부 에이전트는 runtime_bias, 장기 계획, 체크리스트 제안만 작성합니다.
- 최종 판단은 AIA policy engine이 수행합니다.
- 최종 실행 검증은 게임 서버가 수행합니다.

## 장점
- 외부 API 비용/의존성 감소
- 데이터가 내부망에 머무름
- 게임 서버 머신 자원 절약
- AIA와 LLM을 독립적으로 확장 가능

## 주의점
- 추론 서버 자원 계획 필요
- 긴 프롬프트/과도한 호출은 지연 증가
- 여전히 최종 액션 실행은 게임 서버가 검증해야 함
