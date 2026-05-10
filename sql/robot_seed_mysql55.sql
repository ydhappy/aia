-- Beginner-safe robot seed data for MySQL 5.5.
-- This file DOES NOT insert directly into robot / robot_item / robot_skill.
-- It inserts pending spawn requests into aia_robot_spawn_request.
-- The game server connector must process these rows and create real robot rows safely.

SET NAMES utf8;

INSERT INTO aia_robot_spawn_request
(request_id, server_name, agent_id, name, class_type, class_id, level, loc_x, loc_y, loc_map, heading, role, style, home_x, home_y, home_map, hunt_zone_id, priority, status, attempts, last_error, metadata_json)
VALUES
('seed-main-royal-0001', 'main', 'aia_royal_0001', 'AIA군주001', 'royal', 0, 10, 32670, 32790, 4, 0, 'leader', 'balanced', 32670, 32790, 4, 'start_field', 100, 'pending', 0, '', '{"source":"robot_seed_mysql55","memo":"beginner royal seed"}'),
('seed-main-knight-0001', 'main', 'aia_knight_0001', 'AIA기사001', 'knight', 1, 10, 32671, 32790, 4, 0, 'tank', 'aggressive', 32670, 32790, 4, 'start_field', 100, 'pending', 0, '', '{"source":"robot_seed_mysql55","memo":"beginner knight seed"}'),
('seed-main-knight-0002', 'main', 'aia_knight_0002', 'AIA기사002', 'knight', 1, 8, 32672, 32790, 4, 0, 'fighter', 'balanced', 32670, 32790, 4, 'start_field', 90, 'pending', 0, '', '{"source":"robot_seed_mysql55","memo":"beginner knight seed"}'),
('seed-main-elf-0001', 'main', 'aia_elf_0001', 'AIA요정001', 'elf', 2, 10, 32669, 32790, 4, 0, 'ranged', 'careful', 32670, 32790, 4, 'start_field', 95, 'pending', 0, '', '{"source":"robot_seed_mysql55","memo":"beginner elf seed"}'),
('seed-main-elf-0002', 'main', 'aia_elf_0002', 'AIA요정002', 'elf', 2, 8, 32668, 32790, 4, 0, 'ranged', 'balanced', 32670, 32790, 4, 'start_field', 85, 'pending', 0, '', '{"source":"robot_seed_mysql55","memo":"beginner elf seed"}'),
('seed-main-wizard-0001', 'main', 'aia_wizard_0001', 'AIA법사001', 'wizard', 3, 10, 32670, 32791, 4, 0, 'support', 'careful', 32670, 32790, 4, 'start_field', 95, 'pending', 0, '', '{"source":"robot_seed_mysql55","memo":"beginner wizard seed"}')
ON DUPLICATE KEY UPDATE
    priority = VALUES(priority),
    metadata_json = VALUES(metadata_json),
    last_error = IF(status = 'done', last_error, ''),
    status = IF(status = 'done', 'done', 'pending');

-- Check seed rows:
-- SELECT uid, request_id, server_name, agent_id, name, class_type, level, status
-- FROM aia_robot_spawn_request
-- WHERE request_id LIKE 'seed-main-%'
-- ORDER BY uid;
