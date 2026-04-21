# Persona Layers

## 목적
로봇의 행동/멘트 톤을 MBTI, 세대 톤, 말투 강도, 관계 거리감, 말투 모드, 줄임말/밈 강도로 세밀하게 조정하기 위한 구조를 설명합니다.

## 설계 원칙
- 자동 추정이 아니라 운영자가 명시적으로 profile metadata에 설정
- 전술 판단 자체보다 멘트/톤/표현/운영 로그 성격에 우선 반영
- 필요 시 일부 meta policy나 style bias에 간접 반영 가능

## metadata 예시 필드
- `mbti`
- `generation`
- `speech_level`
- `relationship`
- `speech_mode`
- `slang_level`
- `meme_level`

## speech_mode 예시
- `standard`
- `banmal`
- `semi_formal`
- `half_honorific`

## slang_level 예시
- `none`
- `light`
- `high`

## meme_level 예시
- `none`
- `light`
- `high`

## 현재 반영 위치
- persona layer service
- talk service
- goal route 응답

## 목적
- 같은 행동이라도 개체별 캐릭터성 차등화
- 운영 로그/멘트/대사 품질 개선
- 반말/존댓말/반존댓말/줄임말/밈 톤 분기 지원
- 파티/길드/상점/NPC 역할별 표현 차별화
