-- AIA robot spawn request queue for MySQL 5.5 / MariaDB legacy servers.
-- This table is a safe bridge table. AIA may insert spawn requests here.
-- The game server must poll pending rows, create the real robot with its own IdFactory/World logic,
-- then mark the row as done or failed.
-- Do not let AIA insert directly into server-owned robot/character tables.

CREATE TABLE IF NOT EXISTS aia_robot_spawn_request (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    request_id VARCHAR(64) NOT NULL DEFAULT '',
    server_name VARCHAR(64) NOT NULL DEFAULT 'default',
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    name VARCHAR(45) NOT NULL DEFAULT '',
    class_type VARCHAR(20) NOT NULL DEFAULT 'knight',
    class_id INT(10) NOT NULL DEFAULT 1,
    level INT(10) NOT NULL DEFAULT 1,
    loc_x INT(10) NOT NULL DEFAULT 0,
    loc_y INT(10) NOT NULL DEFAULT 0,
    loc_map INT(10) NOT NULL DEFAULT 0,
    heading INT(10) NOT NULL DEFAULT 0,
    role VARCHAR(32) NOT NULL DEFAULT 'custom',
    style VARCHAR(32) NOT NULL DEFAULT 'balanced',
    home_x INT(10) NOT NULL DEFAULT 0,
    home_y INT(10) NOT NULL DEFAULT 0,
    home_map INT(10) NOT NULL DEFAULT 0,
    hunt_zone_id VARCHAR(80) NOT NULL DEFAULT '',
    priority INT(10) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts INT(10) NOT NULL DEFAULT 0,
    last_error VARCHAR(255) NOT NULL DEFAULT '',
    metadata_json LONGTEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    claimed_at DATETIME NULL DEFAULT NULL,
    done_at DATETIME NULL DEFAULT NULL,
    PRIMARY KEY (uid),
    UNIQUE KEY uq_aia_robot_spawn_request_id (request_id),
    KEY idx_aia_robot_spawn_status (status, priority, uid),
    KEY idx_aia_robot_spawn_agent (agent_id),
    KEY idx_aia_robot_spawn_server (server_name, status, uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Example request.
-- INSERT INTO aia_robot_spawn_request
-- (request_id, server_name, agent_id, name, class_type, class_id, level, loc_x, loc_y, loc_map, role, style, home_x, home_y, home_map, hunt_zone_id, priority, metadata_json)
-- VALUES
-- ('boot-robot-0001', 'main', 'aia_robot_0001', '기사로봇0001', 'knight', 1, 10, 32670, 32790, 4, 'tank', 'balanced', 32670, 32790, 4, 'gludio_field_roam', 100, '{"source":"aia_bootstrap"}');
