# Agent Architecture

AIA now includes a lightweight agent orchestration layer.

## Flow
1. Load robot profile
2. Load recent robot events
3. Build runtime trace with agent graph
4. Estimate risk score
5. Choose strategy
6. Optionally request an LLM hint
7. Parse safe JSON decision if available
8. Validate final action
9. Return one allowed action only

## Why this is useful
- Easier debugging
- Better consistency across roles
- Safer optional LLM usage
- Clear fallback path

## Trace endpoint
`GET /robot/{agent_id}/trace`

This returns the latest reasoning trace, including:
- risk score
- chosen strategy
- whether LLM hint was requested
- final source
- final reason

## Design rule
The trace is diagnostic metadata. It must not directly execute game actions.
