package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

public class ServerRobotStore {
    private final String jdbcUrl;
    private final String user;
    private final String password;

    public ServerRobotStore(String jdbcUrl, String user, String password) {
        this.jdbcUrl = normalizeJdbcUrl(jdbcUrl);
        this.user = user;
        this.password = password;
    }

    public boolean existsByAgentIdOrName(String agentId, String name) throws Exception {
        Connection conn = openConnection();
        try {
            PreparedStatement ps = conn.prepareStatement(
                    "SELECT robot_uid FROM server_robot WHERE deleted = 0 AND (agent_id = ? OR name = ?) LIMIT 1"
            );
            try {
                ps.setString(1, safe(agentId));
                ps.setString(2, safe(name));
                ResultSet rs = ps.executeQuery();
                try {
                    return rs.next();
                } finally {
                    rs.close();
                }
            } finally {
                ps.close();
            }
        } finally {
            closeQuietly(conn);
        }
    }

    public long createRobot(AiaRobotSpawnRequest request, AiaRobotTemplateConfig template, long objectId) throws Exception {
        Connection conn = openConnection();
        try {
            conn.setAutoCommit(false);
            long robotUid = insertRobot(conn, request, template, objectId);
            insertAiState(conn, request, robotUid, objectId);
            insertItems(conn, robotUid, objectId, template.items(request.classType));
            insertSkills(conn, robotUid, template.skills(request.classType));
            insertLog(conn, robotUid, objectId, request.agentId, "spawn", "server_robot_created", request.locX, request.locY, request.locMap);
            conn.commit();
            return robotUid;
        } catch (Exception e) {
            rollbackQuietly(conn);
            throw e;
        } finally {
            closeQuietly(conn);
        }
    }

    public void updateAiState(long robotUid, String action, String reason, String error) throws Exception {
        Connection conn = openConnection();
        try {
            PreparedStatement ps = conn.prepareStatement(
                    "UPDATE server_robot_ai_state "
                            + "SET current_action = ?, last_decision = ?, last_reason = ?, last_error = ?, last_tick_at = NOW() "
                            + "WHERE robot_uid = ?"
            );
            try {
                ps.setString(1, safe(action));
                ps.setString(2, safe(action));
                ps.setString(3, safe(reason));
                ps.setString(4, safe(error));
                ps.setLong(5, robotUid);
                ps.executeUpdate();
            } finally {
                ps.close();
            }
        } finally {
            closeQuietly(conn);
        }
    }

    public void log(long robotUid, long objectId, String agentId, String logType, String message, int x, int y, int map) throws Exception {
        Connection conn = openConnection();
        try {
            insertLog(conn, robotUid, objectId, agentId, logType, message, x, y, map);
        } finally {
            closeQuietly(conn);
        }
    }

    private long insertRobot(Connection conn, AiaRobotSpawnRequest request, AiaRobotTemplateConfig template, long objectId) throws Exception {
        PreparedStatement ps = conn.prepareStatement(
                "INSERT INTO server_robot "
                        + "(object_id, agent_id, name, class_type, class_id, level, hp, max_hp, mp, max_mp, "
                        + "loc_x, loc_y, loc_map, heading, home_x, home_y, home_map, role, style, ai_enabled, online_state, deleted, last_spawn_at) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 0, NOW())",
                Statement.RETURN_GENERATED_KEYS
        );
        try {
            int classId = template.classId(request.classType, request.classId);
            int hp = template.spawnHp(request.classType, 100);
            int mp = template.spawnMp(request.classType, 30);
            ps.setLong(1, objectId);
            ps.setString(2, safe(request.agentId));
            ps.setString(3, safe(request.name));
            ps.setString(4, safe(request.classType));
            ps.setInt(5, classId);
            ps.setInt(6, request.level);
            ps.setInt(7, hp);
            ps.setInt(8, hp);
            ps.setInt(9, mp);
            ps.setInt(10, mp);
            ps.setInt(11, request.locX);
            ps.setInt(12, request.locY);
            ps.setInt(13, request.locMap);
            ps.setInt(14, request.heading);
            ps.setInt(15, request.homeX);
            ps.setInt(16, request.homeY);
            ps.setInt(17, request.homeMap);
            ps.setString(18, safe(request.role));
            ps.setString(19, safe(request.style));
            ps.executeUpdate();
            ResultSet keys = ps.getGeneratedKeys();
            try {
                if (keys.next()) {
                    return keys.getLong(1);
                }
            } finally {
                keys.close();
            }
            throw new IllegalStateException("server_robot insert did not return generated key");
        } finally {
            ps.close();
        }
    }

    private void insertAiState(Connection conn, AiaRobotSpawnRequest request, long robotUid, long objectId) throws Exception {
        PreparedStatement ps = conn.prepareStatement(
                "INSERT INTO server_robot_ai_state "
                        + "(robot_uid, object_id, agent_id, current_action, hp_percent, mp_percent, safe_zone, last_decision, last_tick_at) "
                        + "VALUES (?, ?, ?, 'IDLE', 100, 100, 0, 'IDLE', NOW())"
        );
        try {
            ps.setLong(1, robotUid);
            ps.setLong(2, objectId);
            ps.setString(3, safe(request.agentId));
            ps.executeUpdate();
        } finally {
            ps.close();
        }
    }

    private void insertItems(Connection conn, long robotUid, long objectId, int[] itemIds) throws Exception {
        if (itemIds == null || itemIds.length == 0) {
            return;
        }
        PreparedStatement ps = conn.prepareStatement(
                "INSERT INTO server_robot_item (robot_uid, object_id, item_id, count, equipped) VALUES (?, ?, ?, 1, 0)"
        );
        try {
            for (int i = 0; i < itemIds.length; i++) {
                ps.setLong(1, robotUid);
                ps.setLong(2, objectId);
                ps.setInt(3, itemIds[i]);
                ps.addBatch();
            }
            ps.executeBatch();
        } finally {
            ps.close();
        }
    }

    private void insertSkills(Connection conn, long robotUid, int[] skillIds) throws Exception {
        if (skillIds == null || skillIds.length == 0) {
            return;
        }
        PreparedStatement ps = conn.prepareStatement(
                "INSERT IGNORE INTO server_robot_skill (robot_uid, skill_id, skill_level, enabled) VALUES (?, ?, 1, 1)"
        );
        try {
            for (int i = 0; i < skillIds.length; i++) {
                ps.setLong(1, robotUid);
                ps.setInt(2, skillIds[i]);
                ps.addBatch();
            }
            ps.executeBatch();
        } finally {
            ps.close();
        }
    }

    private void insertLog(Connection conn, long robotUid, long objectId, String agentId, String logType, String message, int x, int y, int map) throws Exception {
        PreparedStatement ps = conn.prepareStatement(
                "INSERT INTO server_robot_log (robot_uid, object_id, agent_id, log_type, message, loc_x, loc_y, loc_map) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        );
        try {
            ps.setLong(1, robotUid);
            ps.setLong(2, objectId);
            ps.setString(3, safe(agentId));
            ps.setString(4, safe(logType));
            ps.setString(5, safe(message));
            ps.setInt(6, x);
            ps.setInt(7, y);
            ps.setInt(8, map);
            ps.executeUpdate();
        } finally {
            ps.close();
        }
    }

    private Connection openConnection() throws Exception {
        return DriverManager.getConnection(jdbcUrl, user, password);
    }

    private String normalizeJdbcUrl(String value) {
        if (value == null) {
            return "";
        }
        String lower = value.toLowerCase();
        if (!lower.startsWith("jdbc:mysql://") && !lower.startsWith("jdbc:mariadb://")) {
            return value;
        }
        String result = value;
        if (result.indexOf('?') < 0) {
            result += "?useUnicode=true&characterEncoding=utf8";
        } else {
            if (lower.indexOf("useunicode=") < 0) {
                result += "&useUnicode=true";
            }
            if (lower.indexOf("characterencoding=") < 0) {
                result += "&characterEncoding=utf8";
            }
        }
        return result;
    }

    private String safe(String value) {
        return value == null ? "" : value;
    }

    private void rollbackQuietly(Connection conn) {
        if (conn != null) {
            try {
                conn.rollback();
            } catch (Exception ignored) {
            }
        }
    }

    private void closeQuietly(Connection conn) {
        if (conn != null) {
            try {
                conn.close();
            } catch (Exception ignored) {
            }
        }
    }
}
