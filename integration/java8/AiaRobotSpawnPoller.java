package integration.java8;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
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
        this.jdbcUrl = jdbcUrl;
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

    private List<AiaRobotSpawnRequest> claimPendingRequests() throws Exception {
        List<Long> ids = new ArrayList<Long>();
        List<Long> claimedIds = new ArrayList<Long>();
        List<AiaRobotSpawnRequest> rows = new ArrayList<AiaRobotSpawnRequest>();
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
            conn.setAutoCommit(false);
            PreparedStatement select = conn.prepareStatement(
                    "SELECT uid FROM aia_robot_spawn_request "
                            + "WHERE status = 'pending' AND server_name = ? "
                            + "ORDER BY priority DESC, uid ASC LIMIT ?"
            );
            select.setString(1, serverName);
            select.setInt(2, batchSize);
            ResultSet rs = select.executeQuery();
            while (rs.next()) {
                ids.add(Long.valueOf(rs.getLong("uid")));
            }
            rs.close();
            select.close();

            PreparedStatement claim = conn.prepareStatement(
                    "UPDATE aia_robot_spawn_request "
                            + "SET status = 'claimed', attempts = attempts + 1, claimed_at = NOW() "
                            + "WHERE uid = ? AND status = 'pending'"
            );
            for (Long id : ids) {
                claim.setLong(1, id.longValue());
                if (claim.executeUpdate() == 1) {
                    claimedIds.add(id);
                }
            }
            claim.close();
            conn.commit();
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
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
            PreparedStatement fetch = conn.prepareStatement(
                    "SELECT * FROM aia_robot_spawn_request "
                            + "WHERE uid = ? AND status = 'claimed' AND server_name = ?"
            );
            fetch.setLong(1, uid);
            fetch.setString(2, serverName);
            ResultSet rs = fetch.executeQuery();
            AiaRobotSpawnRequest request = null;
            if (rs.next()) {
                request = AiaRobotSpawnRequest.from(rs);
            }
            rs.close();
            fetch.close();
            return request;
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
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
            PreparedStatement ps = conn.prepareStatement(
                    "UPDATE aia_robot_spawn_request "
                            + "SET status = 'done', done_at = NOW(), last_error = ? "
                            + "WHERE uid = ?"
            );
            ps.setString(1, message + ":" + serverObjectId);
            ps.setLong(2, uid);
            ps.executeUpdate();
            ps.close();
        }
    }

    private void markFailed(long uid, String error) throws Exception {
        String message = error == null ? "unknown_error" : error;
        if (message.length() > 250) {
            message = message.substring(0, 250);
        }
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password)) {
            PreparedStatement ps = conn.prepareStatement(
                    "UPDATE aia_robot_spawn_request "
                            + "SET status = 'failed', last_error = ? "
                            + "WHERE uid = ?"
            );
            ps.setString(1, message);
            ps.setLong(2, uid);
            ps.executeUpdate();
            ps.close();
        }
    }
}
