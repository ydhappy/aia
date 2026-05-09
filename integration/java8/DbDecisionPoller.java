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
        this.jdbcUrl = normalizeMysqlJdbcUrl(jdbcUrl);
        this.user = user;
        this.password = password;
    }

    public String latestDecisionAction(String agentId) throws Exception {
        Connection conn = null;
        PreparedStatement ps = null;
        ResultSet rs = null;
        try {
            conn = DriverManager.getConnection(jdbcUrl, user, password);
            ps = conn.prepareStatement(
                    "SELECT action FROM aia_robot_decision WHERE agent_id = ? ORDER BY uid DESC LIMIT 1"
            );
            ps.setString(1, agentId);
            rs = ps.executeQuery();
            if (rs.next()) {
                return rs.getString(1);
            }
            return null;
        } finally {
            if (rs != null) {
                rs.close();
            }
            if (ps != null) {
                ps.close();
            }
            if (conn != null) {
                conn.close();
            }
        }
    }

    private String normalizeMysqlJdbcUrl(String value) {
        if (value == null) {
            return "";
        }
        String lower = value.toLowerCase();
        if (!lower.startsWith("jdbc:mysql://")) {
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
}
