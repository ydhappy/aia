# Integration Summary

AIA supports multiple game server stacks through HTTP JSON.

## Supported styles
- Java 8 / Java 17
- C++
- C#
- Go
- Node.js
- Python

## Main APIs
- `POST /observe`
- `POST /decide`
- `POST /observe/batch`
- `POST /decide/batch`
- `POST /robot/profile`
- `POST /robot/event`
- `GET /robot/{agent_id}`
- `GET /robot/{agent_id}/trace`

## Recommended production setup
- rule engine primary
- optional LLM hints
- API key auth enabled
- batch mode enabled for large bot groups
- server-side validation always required

## Example assets
- `docs/java8-client-example.md`
- `examples/python_client.py`
- `examples/node_client.js`
- `examples/go_client.go`
- `examples/csharp_client.cs`
- `docs/cpp-integration-notes.md`
