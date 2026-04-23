package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

/**
 * aia_robot_event 테이블에 중요한 이벤트를 기록합니다.
 *
 * 언제 쓰나:
 * - 로봇이 피격됨
 * - 보스 발견
 * - 희귀 아이템 발견
 * - 과적 발생
 * - 안전지대 진입
 *
 * 초보자 주의:
 * - 현재 DB에 `aia_robot_event` 테이블이 먼저 있어야 합니다.
 * - `sql/aia_robot_schema.sql`를 먼저 적용하세요.
 * - JDBC URL / user / password 는 현재 서버 DB 환경에 맞게 바꾸세요.
 */
public class RobotEventWriter {
    private final String jdbcUrl;
    private final String user;
    private final String password;

    public RobotEventWriter(String jdbcUrl, String user, String password) {
        this.jdbcUrl = jdbcUrl;
        this.user = user;
        this.password = password;
    }

    public void write(String agentId, long tick, String eventType, String severity, String message, String payloadJson) throws Exception {
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
            String sql = "INSERT INTO aia_robot_event (object_id, name, action_type, detail, loc_x, loc_y, loc_map) VALUES (?, ?, ?, ?, ?, ?, ?)";
            PreparedStatement ps = conn.prepareStatement(sql);
            ps.setLong(1, tick);
            ps.setString(2, safeName(agentId));
            ps.setString(3, eventType);
            ps.setString(4, safeDetail(severity, message, payloadJson));
            ps.setInt(5, 0);
            ps.setInt(6, 0);
            ps.setInt(7, 0);
            ps.executeUpdate();
            ps.close();
        }
    }

    private String safeName(String agentId) {
        if (agentId == null || agentId.length() == 0) {
            return "aia_robot";
        }
        return agentId.length() > 45 ? agentId.substring(0, 45) : agentId;
    }

    private String safeDetail(String severity, String message, String payloadJson) {
        String value = (severity == null ? "" : severity) + " " + (message == null ? "" : message);
        if (payloadJson != null && payloadJson.length() > 2) {
            value += " " + payloadJson;
        }
        return value.length() > 255 ? value.substring(0, 255) : value;
    }
}
