# Self-Healing and Auto-Recovery

AIA now includes recovery-oriented components for autonomous operation.

## Goal
When failures, invalid decisions, or unstable states happen, the system should first attempt safe automatic recovery before manual intervention.

## Current recovery behaviors
- low HP -> force retreat recommendation
- invalid decision trace -> pause top automation task
- LLM validation error -> rule-only fallback recommendation
- missing state -> no-op with explicit reason

## Admin APIs
- `GET /admin/robot/{agent_id}`
- `GET /admin/system?agent_ids=...`
- `POST /admin/recover/{agent_id}`

## Design principle
Recovery is conservative.
It should prefer:
- pausing risky automation
- retreating to safety
- falling back to rule-based operation
instead of aggressive retries.

## Important note
This is automatic recovery logic, not guaranteed source-code self-repair. Runtime recovery and safe fallback are implemented. Full autonomous code debugging or patching still requires controlled development workflows.
