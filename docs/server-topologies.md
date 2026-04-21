# Server Topologies

AIA can be deployed in several ways depending on the game server architecture.

## 1. Same host sidecar
- Game server and AIA run on the same machine
- Use localhost HTTP calls
- Best for low latency

## 2. Internal LAN service
- Multiple game servers call one shared AIA instance
- Good for centralized robot policy control
- Use API key auth

## 3. Per-world AIA service
- One AIA instance per game world or shard
- Better isolation
- Easier world-specific tuning

## 4. Batch broker mode
- Game server gathers multiple robot states
- Sends them through `/observe/batch` and `/decide/batch`
- Good for large bot groups

## 5. Hybrid rule + LLM
- Rule engine always enabled
- LLM only for exceptional or high-context decisions
- Recommended production setup

## Recommended default
For most MMORPG servers:
- AIA sidecar or same-LAN deployment
- API key enabled
- batch requests enabled
- rule engine primary
- llama.cpp or no LLM in production until stable
