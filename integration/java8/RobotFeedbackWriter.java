package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

/**
 * aia_robot_feedback 테이블에 행동 결과를 기록합니다.
 *
 * 왜 필요한가:
 * - AIA 학습/성장/실패 분석에 사용됩니다.
 * - 예: 이동 실패가 많으면 안전 모드로 자동 조정 가능
 *
 * 초보자 주의:
 * - 현재 DB에 `aia_robot_feedback` 테이블이 먼저 있어야 합니다.
 * - `sql/aia_robot_schema.sql`를 먼저 적용하세요.
 * - JDBC URL / user / password 는 현재 서버 DB 환경에 맞게 바꾸세요.
 */
public class RobotFeedbackWriter {
    private final String jdbcUrl;
    private final String user;
    private final String password;

    public RobotFeedbackWriter(String jdbcUrl, String user, String password) {
        this.jdbcUrl = jdbcUrl;
        this.user = user;
        this.password = password;
    }

    public void write(String agentId, long tick, String action, double reward, String outcome, int mapId, String contextJson) throws Exception {
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
            String sql = "INSERT INTO aia_robot_feedback (agent_id, tick, action, reward, outcome, map_id, context_json) VALUES (?, ?, ?, ?, ?, ?, ?)";
            PreparedStatement ps = conn.prepareStatement(sql);
            ps.setString(1, agentId);
            ps.setLong(2, tick);
            ps.setString(3, action);
            ps.setDouble(4, reward);
            ps.setString(5, outcome);
            ps.setInt(6, mapId);
            ps.setString(7, contextJson == null ? "{}" : contextJson);
            ps.executeUpdate();
            ps.close();
        }
    }
}
