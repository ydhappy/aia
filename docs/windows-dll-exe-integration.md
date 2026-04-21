# Deprecated Windows DLL and EXE Guidance

## 결론
AIA의 기본 운영 경로는 더 이상 DLL/EXE 중심이 아닙니다.
현재 권장 경로는 Python + Java 8 + script 기반 로컬 분리 실행입니다.

## 현재 권장 구성
- Game Server: Java 8
- AIA Core: Python
- Local runner: `scripts/run_local_aia.py`
- Java adapter: `integration/java8/LocalAiaClient.java`
- DB mixed mode: `integration/java8/DbDecisionPoller.java`

## 전환 원칙
- DLL 호출 대신 local HTTP/runtime bridge 사용
- EXE 패키징 대신 Python runtime execution 사용
- 운영 자동화는 script와 scheduler cycle로 처리

## 참고 문서
- `docs/python-java-script-only.md`
