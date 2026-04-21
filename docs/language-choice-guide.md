# Language Choice Guide

## 결론
AIA 코어는 현재 Python 기반이지만, 게임 서버와 연동 계층은 Python만 고집할 필요가 없습니다.

## 권장 기준
### AIA 코어
- 현재 구현 자산이 가장 많으므로 Python 유지 권장
- FastAPI 기반 운영/관제/학습/자동화 자산 활용 가능

### 게임 서버
다음 언어 모두 연동 가능합니다.
- Java
- C++
- C#
- Go
- Node.js
- Python

## 왜 서버는 다른 언어여도 되는가
AIA는 외부 연동 계층으로 설계되어 있습니다.
연동 방식은 다음 중 하나를 쓰면 됩니다.
- REST API
- WebSocket
- DB bridge
- 혼합 방식

## 권장 실무 구조
- 게임 서버: 기존 언어 유지
- AIA: Python 유지
- 필요 시 게이트웨이/운영툴/UI만 다른 언어 사용

## 언어별 권장 사용처
### Java
- L1J 계열 서버
- 직접 REST 연동
- DB bridge 보조

### C++
- 구형 서버 코어
- 최소 훅 + DB bridge 또는 REST adapter

### C#
- 운영 서버, 매니저, 도구 서버

### Go
- 대규모 게이트웨이, 샤드 조정, 고성능 API 계층

### Node.js / TypeScript
- 운영 UI, 관리자 도구, 웹 계층

### Python
- AIA 코어, AI/학습/자동화/운영 API

## 최종 판단
지금 구조에서는 Python만 써야 하는 것이 아니라,
AIA 코어는 Python,
게임 서버는 기존 언어 유지,
주변 계층은 목적에 따라 혼합하는 것이 가장 현실적이고 완성도가 높습니다.
