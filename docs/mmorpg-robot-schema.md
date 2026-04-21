# MMORPG Robot Schema Reference

## AgentState recommended fields
- `hp`, `mp`
- `x`, `y`, `map_id`, `heading`
- `target_id`, `target_distance`, `target_hp`
- `is_under_attack`
- `nearby_enemies`, `nearby_allies`
- `safe_zone`, `can_teleport`
- `weight_percent`
- `cooldowns`
- `inventory`
- `buffs`, `debuffs`
- `aggro_targets`
- `extras`

## RobotProfile recommended fields
- `role`
- `style`
- `party_id`, `clan_id`
- `home_x`, `home_y`
- `patrol_points`
- `preferred_skills`
- `banned_skills`
- `tags`
- `notes`
- `metadata`

## RobotEvent recommended examples
- `danger_zone`
- `loot_detected`
- `boss_spawn`
- `party_member_down`
- `path_blocked`
- `quest_target_found`
- `safe_zone_reached`
- `return_to_base`

## Practical ingestion rule
Do not send every tiny tick event. Send meaningful changes only:
- target changed
- boss appeared
- danger escalated
- path blocked
- loot detected
- party member down

## Safety principle
The game server remains the final authority for execution. AIA only recommends one next action.
