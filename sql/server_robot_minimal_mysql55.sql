-- Minimal server-owned robot tables for servers that do not have any robot schema yet.
-- MySQL 5.5 compatible: InnoDB, utf8, no JSON type, no generated columns.
-- These tables are owned by the game server, not by AIA.
-- AIA writes spawn requests into aia_robot_spawn_request only.
-- The game server adapter creates rows here during createAndSpawn().

CREATE TABLE IF NOT EXISTS server_robot (
    robot_uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    name VARCHAR(45) NOT NULL DEFAULT '',
    class_type VARCHAR(20) NOT NULL DEFAULT 'knight',
    class_id INT(10) NOT NULL DEFAULT 1,
    level INT(10) NOT NULL DEFAULT 1,
    exp BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    hp INT(10) NOT NULL DEFAULT 100,
    max_hp INT(10) NOT NULL DEFAULT 100,
    mp INT(10) NOT NULL DEFAULT 30,
    max_mp INT(10) NOT NULL DEFAULT 30,
    str_stat INT(10) NOT NULL DEFAULT 10,
    dex_stat INT(10) NOT NULL DEFAULT 10,
    con_stat INT(10) NOT NULL DEFAULT 10,
    int_stat INT(10) NOT NULL DEFAULT 10,
    wis_stat INT(10) NOT NULL DEFAULT 10,
    cha_stat INT(10) NOT NULL DEFAULT 10,
    loc_x INT(10) NOT NULL DEFAULT 0,
    loc_y INT(10) NOT NULL DEFAULT 0,
    loc_map INT(10) NOT NULL DEFAULT 0,
    heading INT(10) NOT NULL DEFAULT 0,
    home_x INT(10) NOT NULL DEFAULT 0,
    home_y INT(10) NOT NULL DEFAULT 0,
    home_map INT(10) NOT NULL DEFAULT 0,
    role VARCHAR(32) NOT NULL DEFAULT 'custom',
    style VARCHAR(32) NOT NULL DEFAULT 'balanced',
    ai_enabled TINYINT(1) NOT NULL DEFAULT 1,
    online_state TINYINT(1) NOT NULL DEFAULT 0,
    deleted TINYINT(1) NOT NULL DEFAULT 0,
    last_spawn_at DATETIME NULL DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (robot_uid),
    UNIQUE KEY uq_server_robot_object (object_id),
    UNIQUE KEY uq_server_robot_agent (agent_id),
    UNIQUE KEY uq_server_robot_name (name),
    KEY idx_server_robot_class (class_type, class_id),
    KEY idx_server_robot_map (loc_map, loc_x, loc_y),
    KEY idx_server_robot_ai (ai_enabled, deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS server_robot_item (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    robot_uid BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    item_id INT(10) NOT NULL DEFAULT 0,
    item_name VARCHAR(80) NOT NULL DEFAULT '',
    count INT(10) NOT NULL DEFAULT 1,
    equipped TINYINT(1) NOT NULL DEFAULT 0,
    enchant_level INT(10) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_server_robot_item_robot (robot_uid),
    KEY idx_server_robot_item_object (object_id),
    KEY idx_server_robot_item_item (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS server_robot_skill (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    robot_uid BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    skill_id INT(10) NOT NULL DEFAULT 0,
    skill_name VARCHAR(80) NOT NULL DEFAULT '',
    skill_level INT(10) NOT NULL DEFAULT 1,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    UNIQUE KEY uq_server_robot_skill (robot_uid, skill_id),
    KEY idx_server_robot_skill_id (skill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS server_robot_ai_state (
    robot_uid BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    current_action VARCHAR(32) NOT NULL DEFAULT 'IDLE',
    target_id VARCHAR(64) NOT NULL DEFAULT '',
    target_object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    target_distance INT(10) NOT NULL DEFAULT 0,
    hp_percent INT(10) NOT NULL DEFAULT 100,
    mp_percent INT(10) NOT NULL DEFAULT 100,
    weight_percent INT(10) NOT NULL DEFAULT 0,
    nearby_enemies INT(10) NOT NULL DEFAULT 0,
    nearby_allies INT(10) NOT NULL DEFAULT 0,
    safe_zone TINYINT(1) NOT NULL DEFAULT 0,
    last_decision VARCHAR(32) NOT NULL DEFAULT 'IDLE',
    last_reason VARCHAR(255) NOT NULL DEFAULT '',
    last_error VARCHAR(255) NOT NULL DEFAULT '',
    last_tick_at DATETIME NULL DEFAULT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (robot_uid),
    KEY idx_server_robot_ai_agent (agent_id),
    KEY idx_server_robot_ai_action (current_action),
    KEY idx_server_robot_ai_tick (last_tick_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS server_robot_log (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    robot_uid BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    log_type VARCHAR(40) NOT NULL DEFAULT '',
    message VARCHAR(255) NOT NULL DEFAULT '',
    loc_x INT(10) NOT NULL DEFAULT 0,
    loc_y INT(10) NOT NULL DEFAULT 0,
    loc_map INT(10) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_server_robot_log_robot (robot_uid, created_at),
    KEY idx_server_robot_log_type (log_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
