-- AIA robot database contract for MySQL / MariaDB.
-- Server-owned robot tables stay limited to: robot, robot_clan, robot_setting.
-- AIA-owned tables use the aia_* prefix so operators can audit them safely.
-- DELETE /robot/{agent_id} clears AIA runtime store only; it does not delete these DB bridge rows.
-- Operators may purge aia_* rows manually after backup, but AIA never deletes server-owned robot tables.
-- Recommended production charset is utf8mb4. Legacy utf8 remains for compatibility with older MySQL/MariaDB installs.

CREATE TABLE IF NOT EXISTS aia_robot_state (
    robot_uid INT(10) UNSIGNED NOT NULL,
    name VARCHAR(45) NOT NULL DEFAULT '',
    hp INT(10) NOT NULL DEFAULT 0,
    mp INT(10) NOT NULL DEFAULT 0,
    hp_percent TINYINT(3) UNSIGNED NOT NULL DEFAULT 0,
    ai_status INT(10) NOT NULL DEFAULT 0,
    mode TINYINT(3) NOT NULL DEFAULT -1,
    mode_label VARCHAR(30) NOT NULL DEFAULT '',
    stall_count INT(10) NOT NULL DEFAULT 0,
    nav_fail INT(10) NOT NULL DEFAULT 0,
    last_active DATETIME NULL DEFAULT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (robot_uid),
    KEY idx_aia_robot_state_active (last_active),
    KEY idx_aia_robot_state_mode (mode, ai_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_event (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    name VARCHAR(45) NOT NULL DEFAULT '',
    action_type VARCHAR(40) NOT NULL DEFAULT '',
    detail VARCHAR(255) NOT NULL DEFAULT '',
    loc_x INT(10) NOT NULL DEFAULT 0,
    loc_y INT(10) NOT NULL DEFAULT 0,
    loc_map INT(10) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_event_object (object_id, created_at),
    KEY idx_aia_robot_event_action (action_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_issue (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    robot_uid INT(10) NOT NULL DEFAULT 0,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    name VARCHAR(45) NOT NULL DEFAULT '',
    issue_type VARCHAR(60) NOT NULL DEFAULT '',
    severity ENUM('low','medium','high') NOT NULL DEFAULT 'medium',
    message VARCHAR(255) NOT NULL DEFAULT '',
    source_action VARCHAR(40) NOT NULL DEFAULT '',
    source_uid BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    detail VARCHAR(255) NOT NULL DEFAULT '',
    loc_x INT(10) NOT NULL DEFAULT 0,
    loc_y INT(10) NOT NULL DEFAULT 0,
    loc_map INT(10) NOT NULL DEFAULT 0,
    resolved ENUM('false','true') NOT NULL DEFAULT 'false',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_issue_open (resolved, severity, created_at),
    KEY idx_aia_robot_issue_robot (robot_uid, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_learning (
    robot_uid INT(10) NOT NULL DEFAULT 0,
    preferred_loc_x INT(10) NOT NULL DEFAULT 0,
    preferred_loc_y INT(10) NOT NULL DEFAULT 0,
    preferred_loc_map INT(10) NOT NULL DEFAULT -1,
    preferred_level INT(10) NOT NULL DEFAULT 0,
    hunt_success_count INT(10) NOT NULL DEFAULT 0,
    death_count INT(10) NOT NULL DEFAULT 0,
    confidence INT(10) NOT NULL DEFAULT 0,
    caution INT(10) NOT NULL DEFAULT 0,
    evolution_stage INT(10) NOT NULL DEFAULT 0,
    roam_radius INT(10) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (robot_uid),
    KEY idx_aia_robot_learning_map (preferred_loc_map)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_stall (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    name VARCHAR(45) NOT NULL DEFAULT '',
    level INT(11) NOT NULL DEFAULT 0,
    pos_x INT(11) NOT NULL DEFAULT 0,
    pos_y INT(11) NOT NULL DEFAULT 0,
    pos_map INT(11) NOT NULL DEFAULT 0,
    home_x INT(11) NOT NULL DEFAULT 0,
    home_y INT(11) NOT NULL DEFAULT 0,
    home_map INT(11) NOT NULL DEFAULT 0,
    stall_ms INT(11) NOT NULL DEFAULT 0,
    nav_fail TINYINT(4) NOT NULL DEFAULT 0,
    roam_fail TINYINT(4) NOT NULL DEFAULT 0,
    walk_fail TINYINT(4) NOT NULL DEFAULT 0,
    fix_type VARCHAR(32) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_stall_object (object_id, created_at),
    KEY idx_aia_robot_stall_map (pos_map, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_autofix (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    object_id BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    name VARCHAR(45) NOT NULL DEFAULT '',
    fix_type VARCHAR(32) NOT NULL DEFAULT '',
    before_x INT(11) NOT NULL DEFAULT 0,
    before_y INT(11) NOT NULL DEFAULT 0,
    before_map INT(11) NOT NULL DEFAULT 0,
    after_x INT(11) NOT NULL DEFAULT 0,
    after_y INT(11) NOT NULL DEFAULT 0,
    after_map INT(11) NOT NULL DEFAULT 0,
    detail VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_autofix_object (object_id, created_at),
    KEY idx_aia_robot_autofix_type (fix_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_metric (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    period_time DATETIME NOT NULL,
    total_active INT(11) NOT NULL DEFAULT 0,
    total_map0 INT(11) NOT NULL DEFAULT 0,
    total_map4 INT(11) NOT NULL DEFAULT 0,
    total_other INT(11) NOT NULL DEFAULT 0,
    stall_detected INT(11) NOT NULL DEFAULT 0,
    stall_fixed INT(11) NOT NULL DEFAULT 0,
    nav_attempt INT(11) NOT NULL DEFAULT 0,
    nav_success INT(11) NOT NULL DEFAULT 0,
    nav_fail INT(11) NOT NULL DEFAULT 0,
    combat_events INT(11) NOT NULL DEFAULT 0,
    death_events INT(11) NOT NULL DEFAULT 0,
    shop_events INT(11) NOT NULL DEFAULT 0,
    reloc_events INT(11) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    UNIQUE KEY uq_aia_robot_metric_period (period_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_world_hunt_guide (
    guide_id VARCHAR(80) NOT NULL,
    map_id INT(10) NOT NULL DEFAULT 0,
    anchor_x INT(10) NOT NULL DEFAULT 0,
    anchor_y INT(10) NOT NULL DEFAULT 0,
    min_level INT(10) NOT NULL DEFAULT 1,
    max_level INT(10) NOT NULL DEFAULT 99,
    recommended_level INT(10) NOT NULL DEFAULT 1,
    guide_type VARCHAR(20) NOT NULL DEFAULT 'normal',
    boss VARCHAR(5) NOT NULL DEFAULT 'false',
    sample_name VARCHAR(80) NOT NULL DEFAULT '',
    weight INT(10) NOT NULL DEFAULT 1,
    source VARCHAR(80) NOT NULL DEFAULT 'monster_spawnlist',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (guide_id),
    KEY idx_aia_world_hunt_map_level (map_id, min_level, max_level),
    KEY idx_aia_world_hunt_type (guide_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_world_siege_guide (
    kingdom_uid INT(10) NOT NULL DEFAULT 0,
    name VARCHAR(80) NOT NULL DEFAULT '',
    x INT(10) NOT NULL DEFAULT 0,
    y INT(10) NOT NULL DEFAULT 0,
    map INT(10) NOT NULL DEFAULT 0,
    throne_x INT(10) NOT NULL DEFAULT 0,
    throne_y INT(10) NOT NULL DEFAULT 0,
    throne_map INT(10) NOT NULL DEFAULT 0,
    owner_clan_id INT(10) NOT NULL DEFAULT 0,
    owner_clan_name VARCHAR(80) NOT NULL DEFAULT '',
    war VARCHAR(5) NOT NULL DEFAULT 'false',
    strategy_json TEXT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (kingdom_uid),
    KEY idx_aia_world_siege_war (war)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_feedback (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    tick BIGINT(20) NULL,
    action VARCHAR(32) NOT NULL DEFAULT '',
    reward DOUBLE NULL,
    outcome VARCHAR(32) NULL,
    map_id INT(10) NOT NULL DEFAULT 0,
    context_json LONGTEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_feedback_agent (agent_id, created_at),
    KEY idx_aia_robot_feedback_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_decision (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    tick BIGINT(20) NULL,
    action VARCHAR(32) NOT NULL DEFAULT '',
    action_args_json LONGTEXT NULL,
    confidence DOUBLE NULL,
    source VARCHAR(64) NULL,
    reason VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_decision_agent (agent_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS aia_robot_trace_summary (
    uid BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    agent_id VARCHAR(64) NOT NULL DEFAULT '',
    tick BIGINT(20) NULL,
    trace_json LONGTEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid),
    KEY idx_aia_robot_trace_agent (agent_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
