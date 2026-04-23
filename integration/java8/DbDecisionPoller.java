package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

public class DbDecisionPoller {
    private final String jdbcUrl;
    private final String user;
    private final String password;

    public DbDecisionPoller(String jdbcUrl, String user, String password) {
        this.jdbcUrl = jdbcUrl;
        this.user = user;
        this.password = password;
    }

    public String latestDecisionAction(String agentId) throws Exception {
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
            PreparedStatement ps = conn.prepareStatement(
                    "SELECT action FROM aia_robot_decision WHERE agent_id = ? ORDER BY uid DESC LIMIT 1"
            );
            ps.setString(1, agentId);
            ResultSet rs = ps.executeQuery();
            if (rs.next()) {
                return rs.getString(1);
            }
            return null;
        }
    }
}
