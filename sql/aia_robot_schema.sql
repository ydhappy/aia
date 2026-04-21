-- AIA robot integration schema
-- Recommended for MySQL / MariaDB compatible environments

CREATE TABLE IF NOT EXISTS robot_state (
    agent_id VARCHAR(64) PRIMARY KEY,
    tick BIGINT NULL,
    hp INT NULL,
    mp INT NULL,
    x INT NULL,
    y INT NULL,
    map_id INT NULL,
    target_id VARCHAR(64) NULL,
    target_distance INT NULL,
    safe_zone TINYINT(1) NULL,
    weight_percent INT NULL,
    payload_json LONGTEXT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS robot_event (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    tick BIGINT NULL,
    event_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NULL,
    message VARCHAR(255) NULL,
    payload_json LONGTEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_robot_event_agent_created (agent_id, created_at),
    INDEX idx_robot_event_type (event_type)
);

CREATE TABLE IF NOT EXISTS robot_feedback (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    tick BIGINT NULL,
    action VARCHAR(32) NOT NULL,
    reward DOUBLE NULL,
    outcome VARCHAR(32) NULL,
    map_id INT NULL,
    context_json LONGTEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_robot_feedback_agent_created (agent_id, created_at),
    INDEX idx_robot_feedback_action (action)
);

CREATE TABLE IF NOT EXISTS robot_task (
    task_id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    mode VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    priority INT DEFAULT 50,
    conditions_json LONGTEXT NULL,
    parameters_json LONGTEXT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_robot_task_agent_status (agent_id, status)
);

CREATE TABLE IF NOT EXISTS robot_decision (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    tick BIGINT NULL,
    action VARCHAR(32) NOT NULL,
    action_args_json LONGTEXT NULL,
    confidence DOUBLE NULL,
    source VARCHAR(64) NULL,
    reason VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_robot_decision_agent_created (agent_id, created_at)
);

CREATE TABLE IF NOT EXISTS robot_trace_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    tick BIGINT NULL,
    trace_json LONGTEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_robot_trace_agent_created (agent_id, created_at)
);
