package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

/**
 * robot_event 테이블에 중요한 이벤트를 기록합니다.
 *
 * 언제 쓰나:
 * - 로봇이 피격됨
 * - 보스 발견
 * - 희귀 아이템 발견
 * - 과적 발생
 * - 안전지대 진입
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
            String sql = "INSERT INTO robot_event (agent_id, tick, event_type, severity, message, payload_json) VALUES (?, ?, ?, ?, ?, ?)";
            PreparedStatement ps = conn.prepareStatement(sql);
            ps.setString(1, agentId);
            ps.setLong(2, tick);
            ps.setString(3, eventType);
            ps.setString(4, severity);
            ps.setString(5, message);
            ps.setString(6, payloadJson == null ? "{}" : payloadJson);
            ps.executeUpdate();
            ps.close();
        }
    }
}
