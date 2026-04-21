# Dashboard and Operations

## Dashboard APIs
- `POST /dashboard/counts`
- `POST /dashboard/filter`
- `POST /dashboard/shards`
- `GET /dashboard/world-profile/{world_id}`

## Recommended use
- counts: fleet-wide visibility
- filter: extract agents with tasks or learning state
- shards: split agent ids for large-scale orchestration
- world-profile validation: verify world config before rollout

## Basic runbook
1. use `/dashboard/counts` to understand fleet health
2. use `/dashboard/filter` to isolate agents with automation or learning
3. use `/scale/recover` or `/admin/recover-bulk` when a group degrades
4. use `/dashboard/shards` to rebalance large robot sets
5. keep Redis and self-hosted LLM separate from the game host for stability
