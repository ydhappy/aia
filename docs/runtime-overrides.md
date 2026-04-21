# Runtime Overrides

AIA supports runtime overrides through robot profile metadata.

## Location
Store overrides in:
- `profile.metadata.overrides`

## Example structure
```json
{
  "overrides": {
    "maps": {
      "101": {
        "style": "defensive",
        "retreat_hp_threshold": 40,
        "move_mode": "kite"
      },
      "202": {
        "forced_action": "RETREAT",
        "forced_mode": "safe_zone"
      }
    }
  }
}
```

## Supported runtime fields
- `style`
- `role`
- `patrol_points`
- `retreat_hp_threshold`
- `retreat_mode`
- `move_mode`
- `forced_action`
- `forced_mode`

## Current behavior
- override is selected by `map_id`
- selected override is attached to trace
- selected override is also applied inside policy decisions

## Safety note
Runtime overrides can bias or force actions, but server-side action validation still remains mandatory.
