# Multi-language Integration Guide

AIA is designed as an HTTP JSON bridge service, so it can be integrated from different server stacks.

## Supported integration style
- Java 8 / Java 17
- C++
- C#
- Python
- Go
- Node.js

## Common flow
1. Build robot profile once or when configuration changes.
2. Send profile to `POST /robot/profile`.
3. Send runtime events to `POST /robot/event` when meaningful events occur.
4. Send current state to `POST /observe`.
5. Ask for action with `POST /decide`.
6. Validate the returned action on the game server.
7. Execute the action on the server side only.

## Why this model is safe
- The AI server never executes game actions directly.
- The game server always validates coordinates, cooldowns, zones, and targets.
- LLM usage is optional and can be disabled entirely.
- Rule engine remains the primary decision maker.

## Suggested events to ingest
- `danger_zone`
- `loot_detected`
- `boss_spawn`
- `party_member_down`
- `path_blocked`
- `quest_target_found`
- `safe_zone_reached`

## Suggested profile fields
- role
- style
- preferred_skills
- banned_skills
- tags
- notes
- metadata

## Server-side validation checklist
- action is in whitelist
- target exists
- destination is valid
- cooldown is ready
- map allows the action
- bot is not in restricted state
