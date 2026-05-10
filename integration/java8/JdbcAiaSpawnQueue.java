package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class JdbcAiaSpawnQueue implements AiaSpawnQueue {
    private final String jdbcUrl;
    private final String user;
    private final String password;
    private final AiaSpawnQueueSql sql;

    public JdbcAiaSpawnQueue(String jdbcUrl, String user, String password) {
        this(jdbcUrl, user, password, AiaSpawnQueueSql.forJdbcUrl(jdbcUrl));
    }

    public JdbcAiaSpawnQueue(String jdbcUrl, String user, String password, AiaSpawnQueueSql sql) {
        this.jdbcUrl = normalizeJdbcUrl(jdbcUrl);
        this.user = user;
        this.password = password;
        this.sql = sql == null ? AiaSpawnQueueSql.forJdbcUrl(jdbcUrl) : sql;
    }

    public List<AiaRobotSpawnRequest> claimPending(String serverName, int batchSize) throws Exception {
        List<Long> ids = new ArrayList<Long>();
        List<Long> claimedIds = new ArrayList<Long>();
        List<AiaRobotSpawnRequest> rows = new ArrayList<AiaRobotSpawnRequest>();
        Connection conn = null;
        try {
            conn = openConnection();
            conn.setAutoCommit(false);
            PreparedStatement select = conn.prepareStatement(sql.selectPendingSql());
            try {
                bindSelectPending(select, serverName, batchSize);
                ResultSet rs = select.executeQuery();
                try {
                    while (rs.next()) {
                        ids.add(Long.valueOf(rs.getLong("uid")));
                    }
                } finally {
                    rs.close();
                }
            } finally {
                select.close();
            }

            PreparedStatement claim = conn.prepareStatement(sql.claimOneSql());
            try {
                for (Long id : ids) {
                    claim.setLong(1, id.longValue());
                    if (claim.executeUpdate() == 1) {
                        claimedIds.add(id);
                    }
                }
            } finally {
                claim.close();
            }
            conn.commit();
        } catch (Exception e) {
            rollbackQuietly(conn);
            throw e;
        } finally {
            closeQuietly(conn);
        }

        for (Long id : claimedIds) {
            AiaRobotSpawnRequest request = fetchClaimedRequest(id.longValue(), serverName);
            if (request != null) {
                rows.add(request);
            }
        }
        return rows;
    }

    public void markDone(long uid, long serverObjectId, String message) throws Exception {
        Connection conn = openConnection();
        try {
            PreparedStatement ps = conn.prepareStatement(sql.markDoneSql());
            try {
                ps.setString(1, safeMessage(message) + ":" + serverObjectId);
                ps.setLong(2, uid);
                ps.executeUpdate();
            } finally {
                ps.close();
            }
        } finally {
            closeQuietly(conn);
        }
    }

    public void markFailed(long uid, String error) throws Exception {
        Connection conn = openConnection();
        try {
            PreparedStatement ps = conn.prepareStatement(sql.markFailedSql());
            try {
                ps.setString(1, safeMessage(error));
                ps.setLong(2, uid);
                ps.executeUpdate();
            } finally {
                ps.close();
            }
        } finally {
            closeQuietly(conn);
        }
    }

    private AiaRobotSpawnRequest fetchClaimedRequest(long uid, String serverName) throws Exception {
        Connection conn = openConnection();
        try {
            PreparedStatement fetch = conn.prepareStatement(sql.fetchClaimedSql());
            try {
                fetch.setLong(1, uid);
                fetch.setString(2, serverName);
                ResultSet rs = fetch.executeQuery();
                try {
                    if (rs.next()) {
                        return AiaRobotSpawnRequest.from(rs);
                    }
                    return null;
                } finally {
                    rs.close();
                }
            } finally {
                fetch.close();
            }
        } finally {
            closeQuietly(conn);
        }
    }

    private void bindSelectPending(PreparedStatement select, String serverName, int batchSize) throws SQLException {
        if (sql.usesTopLimit()) {
            select.setInt(1, batchSize);
            select.setString(2, serverName);
        } else {
            select.setString(1, serverName);
            select.setInt(2, batchSize);
        }
    }

    private Connection openConnection() throws SQLException {
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

    private String safeMessage(String value) {
        String message = value == null ? "unknown" : value;
        if (message.length() > 250) {
            message = message.substring(0, 250);
        }
        return message;
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
