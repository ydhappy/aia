# Ops Run Cycle

## Ops APIs
- `POST /ops/scheduler/run`
- `GET /ops/memory/{agent_id}`

## Recommended periodic cycle
1. select robot ids by shard or fleet batch
2. run scheduler cycle to apply automated recovery checks
3. use dashboard counts to see overall health
4. use memory summary for targeted agents when tuning policies

## Purpose
- periodic stability checks
- conservative auto-recovery
- compact long-term memory view for operations
