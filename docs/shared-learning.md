# Shared Learning

AIA can merge individual robot learning with shared group learning.

## Group key recommendation
Use one of:
- `party_id`
- role name
- custom operational group id

## Current behavior
- robot-specific learning is loaded first
- shared group learning can supplement preferred or avoided actions
- merged result is attached to runtime trace
- feedback can automatically update shared learning when `group_key`, `party_id`, or `role` is supplied in feedback context

## Recommended use
- bots in the same party
- same hunting zone squads
- same role clusters such as healer/tank groups

## Safety rule
Group learning should bias confidence, not replace hard safety rules or server-side validation.
