package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

/**
 * aia_robot_state 테이블에 현재 상태를 기록하는 클래스입니다.
 *
 * 초보자용 설명:
 * - 이 클래스는 DB 연결만 맞으면 바로 쓸 수 있습니다.
 * - JDBC URL / user / password 만 현재 서버 환경에 맞게 바꾸면 됩니다.
 * - 이 예시는 MySQL / MariaDB 기준으로 REPLACE INTO를 사용합니다.
 * - PostgreSQL을 쓴다면 INSERT ... ON CONFLICT ... DO UPDATE 형태로 바꿔야 합니다.
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
            String sql = "INSERT INTO aia_robot_state "
                    + "(robot_uid, name, hp, mp, hp_percent, ai_status, mode, mode_label, last_active) "
                    + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW()) "
                    + "ON DUPLICATE KEY UPDATE "
                    + "name=VALUES(name), hp=VALUES(hp), mp=VALUES(mp), hp_percent=VALUES(hp_percent), "
                    + "ai_status=VALUES(ai_status), mode=VALUES(mode), mode_label=VALUES(mode_label), last_active=NOW()";
            PreparedStatement ps = conn.prepareStatement(sql);
            ps.setInt(1, s.robotUid > 0 ? s.robotUid : stableRobotUid(s.agentId));
            ps.setString(2, safeName(s.agentId));
            ps.setInt(3, s.hp);
            ps.setInt(4, s.mp);
            ps.setInt(5, Math.max(0, Math.min(100, s.hp)));
            ps.setInt(6, 0);
            ps.setInt(7, -1);
            ps.setString(8, "AIA");
            ps.executeUpdate();
            ps.close();
        }
    }

    private int stableRobotUid(String agentId) {
        if (agentId == null || agentId.length() == 0) {
            return 1;
        }
        int hash = agentId.hashCode() & 0x7fffffff;
        return Math.max(1, hash % 2000000000);
    }

    private String safeName(String agentId) {
        if (agentId == null || agentId.length() == 0) {
            return "aia_robot";
        }
        return agentId.length() > 45 ? agentId.substring(0, 45) : agentId;
    }
}
