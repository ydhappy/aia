# Autonomous Progression

AIA now exposes a progression view for each robot.

## Goal API
- `GET /goal/{agent_id}`

## Included sections
- goal state
- state machine phase
- economy loop step
- npc interaction step

## Purpose
This API helps operations and server integration layers understand what the robot is trying to do next at a higher level than a single tactical action.

## Typical progression
- combat
- overweight detection
- return to safe area
- inventory reset
- resupply
- redeploy
- resume combat or support loop
