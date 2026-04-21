# C++ Integration Notes

AIA can be called from a C++ server through ordinary HTTP JSON requests.

## Recommended flow
1. Send robot profile once at spawn or configuration load.
2. Send meaningful events only.
3. Send current state.
4. Request one next action.
5. Validate and execute on the C++ game server.

## Recommended libraries
- libcurl for HTTP
- nlohmann/json for JSON

## Validation checklist on the C++ server
- action is whitelisted
- target is alive and reachable
- coordinate is valid
- skill cooldown is ready
- movement path is safe
- current map allows the action

## Fail-safe rule
If AIA times out or returns an invalid action, execute a conservative fallback such as `IDLE` or a server-side retreat routine.
