# Scale Guide

## 10 to 100 robots
- direct observe/decide or unified sync
- single AIA instance is often enough

## 100 to 1000 robots
- batch APIs recommended
- Redis recommended
- self-hosted LLM separated from game host

## 1000 to 10000 robots
- shard by world, map, or party cluster
- use `/scale/batches`
- use `/scale/recover`
- keep LLM usage selective
- prefer rule-engine dominant mode

## Useful APIs
- `POST /scale/batches`
- `POST /scale/summary`
- `POST /scale/recover`
- `POST /api/v1/robot/sync`

## Operational rule
Automation handles long-horizon objective, rule engine handles tactical action, and game server still validates final execution.
