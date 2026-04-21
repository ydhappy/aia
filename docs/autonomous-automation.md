# Autonomous Automation System

AIA can be extended from single-step action decisions to multi-step autonomous automation.

## Core idea
Robots do not just choose one action. They can also run long-lived operational tasks such as:
- farming loops
- patrol loops
- escort routines
- support loops
- loot cycles
- return and resume flows

## API
- `POST /automation/task`
- `GET /automation/{agent_id}/tasks`
- `GET /automation/{agent_id}/next-step`

## Recommended operational flow
1. register robot profile
2. register automation task
3. keep sending observe/decide
4. periodically read next-step for long-horizon objective
5. feed action outcomes back into robot learning

## Design principle
- automation handles high-level objective flow
- rule engine handles local tactical action
- server still validates and executes final actions

## Typical usage
### farm loop
- task mode: `farm`
- condition: stop when hp below threshold
- next-step objective: hunt and loot in area

### patrol loop
- task mode: `patrol`
- next-step objective: cycle through patrol points

### return and resume
- task mode: `return_and_resume`
- return to safe area, then resume previous loop

## Safety
Automation next-step is guidance metadata. Final game action validation remains mandatory on the game server.
