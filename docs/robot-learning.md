# Robot Learning

AIA supports lightweight robot learning through runtime feedback.

## Purpose
Robots can accumulate action outcomes and adapt preferred or avoided actions over time.

## API
- `POST /robot/feedback`
- `GET /robot/{agent_id}/learning`

## Feedback payload
- `agent_id`
- `tick`
- `action`
- `reward`
- `outcome` = success / partial / failure
- `context`

## Recommended usage
Send feedback after the game server verifies the actual result of an action.

Examples:
- retreat succeeded and survived -> positive reward
- attack failed due to invalid target -> negative reward
- pickup succeeded -> positive reward
- move caused path block -> negative reward

## Current learning model
- action-level reward accumulation
- preferred action extraction
- avoid action extraction
- learning state attached to trace and profile hints

## Important note
This is an online adaptation layer, not full reinforcement learning training. It is designed for immediate operational integration.
