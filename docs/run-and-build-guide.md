# Run and Build Guide

## 결론
현재 AIA는 Python/FastAPI 기반 서비스이므로, 일반적인 의미의 C/C++/Java 바이너리 컴파일이 필수는 아닙니다.

즉, 대부분의 사용자는 다음 둘 중 하나로 사용합니다.
- Python 런타임으로 직접 실행
- Docker/컨테이너로 실행

## 1. Python 직접 실행
### 준비
- Python 3.11 이상 권장
- 가상환경 생성 권장
- `.env.example`를 `.env`로 복사 후 값 수정

### 설치
- `pip install -r requirements.txt`

### 실행
- `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 2. Docker 실행
프로젝트에 Dockerfile 또는 compose가 있으면 컨테이너 방식이 가장 운영에 적합합니다.

권장 구조:
- AIA
- Redis
- Self-Hosted LLM
- Optional DB bridge target DB

## 3. 빌드/컴파일이 필요한가?
### AIA 자체
- Python 서비스이므로 전통적 컴파일은 필수 아님
- 패키지 설치와 런타임 준비가 핵심

### 게임 서버 측
- Java 서버면 jar 빌드 또는 기존 서버 빌드 필요
- C++ 서버면 기존 서버 빌드 필요
- C# 서버면 기존 서버 publish/build 필요

즉, AIA는 보통 컴파일보다 실행 준비가 중요하고,
게임 서버는 각 서버 언어 체계에 맞는 빌드가 필요할 수 있습니다.

## 4. 공용 배포 기준 권장
- 개발자는 로컬에서 Python 실행으로 검증
- 운영자는 Docker 또는 프로세스 매니저(systemd, supervisor 등) 사용
- Redis와 self-hosted LLM은 별도 서비스로 분리

## 5. 최종 판단
현재 상태에서는 AIA를 쓰기 위해 반드시 별도 컴파일 산출물을 만들어야 하는 것은 아닙니다.
대부분은 환경변수 설정 + 의존성 설치 + uvicorn 실행으로 사용 가능합니다.
