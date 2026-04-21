# API Integration

AIA now supports both domain-specific APIs and a unified integration API.

## Unified endpoint
- `POST /api/v1/robot/sync`

## Purpose
Send multiple robot lifecycle updates in one request:
- profile registration
- event ingestion
- observe state update
- feedback learning update
- automation task registration

## Recommended use
Use the unified API from game server gateways or orchestration services that want to minimize request count.

## Example flow
1. register/update profile
2. send recent events
3. send current observe payload
4. optionally send feedback from prior action
5. optionally register or refresh automation task

## Response
The response returns per-section results so the caller can see which part was applied.

## Other APIs remain available
- `/observe`
- `/decide`
- `/robot/profile`
- `/robot/event`
- `/robot/feedback`
- `/automation/task`
- batch APIs
- websocket gateway

## Integration recommendation
- Game server core: keep using narrow tactical APIs if latency is critical
- Gateway or orchestration layer: use unified API to reduce overhead and simplify coordination
