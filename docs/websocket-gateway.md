# WebSocket Gateway

AIA provides a simple WebSocket endpoint at `/ws`.

## Message format
### observe
```json
{
  "type": "observe",
  "body": {
    "agent_id": "bot_001",
    "tick": 1,
    "state": {
      "hp": 90,
      "mp": 20,
      "x": 10,
      "y": 20
    }
  }
}
```

### decide
```json
{
  "type": "decide",
  "body": {
    "agent_id": "bot_001",
    "tick": 2,
    "state": {
      "hp": 90,
      "mp": 20,
      "x": 10,
      "y": 20
    }
  }
}
```

## Response format
- `observe_result`
- `decide_result`
- `error`

## Recommended use
- gateway servers
- proxy processes
- real-time bot farms
- local simulators
