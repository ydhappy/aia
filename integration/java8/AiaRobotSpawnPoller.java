package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class AiaRobotSpawnPoller {
    private final String jdbcUrl;
    private final String user;
    private final String password;
    private final String serverName;
    private final LocalAiaClient aiaClient;
    private final AiaRobotSpawnAdapter adapter;
    private int batchSize = 20;

    public AiaRobotSpawnPoller(
            String jdbcUrl,
            String user,
            String password,
            String serverName,
            LocalAiaClient aiaClient,
            AiaRobotSpawnAdapter adapter
    ) {
        if (adapter == null) {
            throw new IllegalArgumentException("AiaRobotSpawnAdapter is required");
        }
        this.jdbcUrl = normalizeMysqlJdbcUrl(jdbcUrl);
        this.user = user;
        this.password = password;
        this.serverName = serverName == null || serverName.length() == 0 ? "default" : serverName;
        this.aiaClient = aiaClient;
        this.adapter = adapter;
    }

    public void setBatchSize(int batchSize) {
        this.batchSize = Math.max(1, Math.min(batchSize, 200));
    }

    public int runOnce() throws Exception {
        int processed = 0;
        List<AiaRobotSpawnRequest> requests = claimPendingRequests();
        for (AiaRobotSpawnRequest request : requests) {
            processed += processOne(request) ? 1 : 0;
        }
        return processed;
    }

    private Connection openConnection() throws SQLException {
        return DriverManager.getConnection(jdbcUrl, user, password);
    }

    private List<AiaRobotSpawnRequest> claimPendingRequests() throws Exception {
        List<Long> ids = new ArrayList<Long>();
        List<Long> claimedIds = new ArrayList<Long>();
        List<AiaRobotSpawnRequest> rows = new ArrayList<AiaRobotSpawnRequest>();
        Connection conn = null;
        try {
            conn = openConnection();
            conn.setAutoCommit(false);
            PreparedStatement select = conn.prepareStatement(
                    "SELECT uid FROM aia_robot_spawn_request "
                            + "WHERE status = 'pending' AND server_name = ? "
                            + "ORDER BY priority DESC, uid ASC LIMIT ?"
            );
            try {
                select.setString(1, serverName);
                select.setInt(2, batchSize);
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

            PreparedStatement claim = conn.prepareStatement(
                    "UPDATE aia_robot_spawn_request "
                            + "SET status = 'claimed', attempts = attempts + 1, claimed_at = NOW() "
                            + "WHERE uid = ? AND status = 'pending'"
            );
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
            AiaRobotSpawnRequest request = fetchClaimedRequest(id.longValue());
            if (request != null) {
                rows.add(request);
            }
        }
        return rows;
    }

    private AiaRobotSpawnRequest fetchClaimedRequest(long uid) throws Exception {
        Connection conn = openConnection();
        try {
            PreparedStatement fetch = conn.prepareStatement(
                    "SELECT * FROM aia_robot_spawn_request "
                            + "WHERE uid = ? AND status = 'claimed' AND server_name = ?"
            );
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

    private boolean processOne(AiaRobotSpawnRequest request) throws Exception {
        try {
            long serverObjectId;
            if (adapter.exists(request)) {
                serverObjectId = 0L;
                registerAiaProfileSafely(request);
                markDone(request.uid, serverObjectId, "already_exists");
                return true;
            }

            serverObjectId = adapter.createAndSpawn(request);
            adapter.afterSpawn(request, serverObjectId);
            registerAiaProfileSafely(request);
            markDone(request.uid, serverObjectId, "spawned");
            return true;
        } catch (Exception e) {
            markFailed(request.uid, e.getMessage());
            return false;
        }
    }

    private void registerAiaProfileSafely(AiaRobotSpawnRequest request) {
        if (aiaClient == null) {
            return;
        }
        try {
            aiaClient.createRobotProfile(request.toAiaProfileJson());
        } catch (Exception ignored) {
            // The game server owns the real robot. AIA profile registration can be retried later.
        }
    }

    private void markDone(long uid, long serverObjectId, String message) throws Exception {
        Connection conn = openConnection();
        try {
            PreparedStatement ps = conn.prepareStatement(
                    "UPDATE aia_robot_spawn_request "
                            + "SET status = 'done', done_at = NOW(), last_error = ? "
                            + "WHERE uid = ?"
            );
            try {
                ps.setString(1, message + ":" + serverObjectId);
                ps.setLong(2, uid);
                ps.executeUpdate();
            } finally {
                ps.close();
            }
        } finally {
            closeQuietly(conn);
        }
    }

    private void markFailed(long uid, String error) throws Exception {
        String message = error == null ? "unknown_error" : error;
        if (message.length() > 250) {
            message = message.substring(0, 250);
        }
        Connection conn = openConnection();
        try {
            PreparedStatement ps = conn.prepareStatement(
                    "UPDATE aia_robot_spawn_request "
                            + "SET status = 'failed', last_error = ? "
                            + "WHERE uid = ?"
            );
            try {
                ps.setString(1, message);
                ps.setLong(2, uid);
                ps.executeUpdate();
            } finally {
                ps.close();
            }
        } finally {
            closeQuietly(conn);
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
