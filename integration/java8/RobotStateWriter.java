package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

/**
 * robot_state 테이블에 현재 상태를 기록하는 클래스입니다.
 *
 * 초보자용 설명:
 * - 이 클래스는 DB 연결만 맞으면 바로 쓸 수 있습니다.
 * - JDBC URL / user / password 만 현재 서버 환경에 맞게 바꾸면 됩니다.
 * - INSERT가 아니라 REPLACE INTO를 사용해 최신 상태 한 줄만 유지합니다.
 */
public class RobotStateWriter {
    private final String jdbcUrl;
    private final String user;
    private final String password;

    public RobotStateWriter(String jdbcUrl, String user, String password) {
        this.jdbcUrl = jdbcUrl;
        this.user = user;
        this.password = password;
    }

    public void write(RobotStateExtractor.RobotSnapshot s) throws Exception {
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
            String sql = "REPLACE INTO robot_state (agent_id, tick, hp, mp, x, y, map_id, target_id, target_distance, safe_zone, weight_percent, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
            PreparedStatement ps = conn.prepareStatement(sql);
            ps.setString(1, s.agentId);
            ps.setLong(2, s.tick);
            ps.setInt(3, s.hp);
            ps.setInt(4, s.mp);
            ps.setInt(5, s.x);
            ps.setInt(6, s.y);
            ps.setInt(7, s.mapId);
            ps.setString(8, s.targetId);
            ps.setInt(9, s.targetDistance);
            ps.setBoolean(10, s.safeZone);
            ps.setInt(11, s.weightPercent);
            ps.setString(12, "{}");
            ps.executeUpdate();
            ps.close();
        }
    }
}
