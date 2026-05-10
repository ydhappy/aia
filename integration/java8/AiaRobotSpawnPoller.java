package integration.java8;

import java.util.List;

public class AiaRobotSpawnPoller {
    private final String serverName;
    private final LocalAiaClient aiaClient;
    private final AiaRobotSpawnAdapter adapter;
    private final AiaSpawnQueue queue;
    private int batchSize = 20;

    public AiaRobotSpawnPoller(
            String jdbcUrl,
            String user,
            String password,
            String serverName,
            LocalAiaClient aiaClient,
            AiaRobotSpawnAdapter adapter
    ) {
        this(
                new JdbcAiaSpawnQueue(jdbcUrl, user, password),
                serverName,
                aiaClient,
                adapter
        );
    }

    public AiaRobotSpawnPoller(
            AiaSpawnQueue queue,
            String serverName,
            LocalAiaClient aiaClient,
            AiaRobotSpawnAdapter adapter
    ) {
        if (queue == null) {
            throw new IllegalArgumentException("AiaSpawnQueue is required");
        }
        if (adapter == null) {
            throw new IllegalArgumentException("AiaRobotSpawnAdapter is required");
        }
        this.queue = queue;
        this.serverName = serverName == null || serverName.length() == 0 ? "default" : serverName;
        this.aiaClient = aiaClient;
        this.adapter = adapter;
    }

    public void setBatchSize(int batchSize) {
        this.batchSize = Math.max(1, Math.min(batchSize, 500));
    }

    public int runOnce() throws Exception {
        int processed = 0;
        List<AiaRobotSpawnRequest> requests = queue.claimPending(serverName, batchSize);
        for (AiaRobotSpawnRequest request : requests) {
            processed += processOne(request) ? 1 : 0;
        }
        return processed;
    }

    private boolean processOne(AiaRobotSpawnRequest request) throws Exception {
        try {
            long serverObjectId;
            if (adapter.exists(request)) {
                serverObjectId = 0L;
                registerAiaProfileSafely(request);
                queue.markDone(request.uid, serverObjectId, "already_exists");
                return true;
            }

            serverObjectId = adapter.createAndSpawn(request);
            adapter.afterSpawn(request, serverObjectId);
            registerAiaProfileSafely(request);
            queue.markDone(request.uid, serverObjectId, "spawned");
            return true;
        } catch (Exception e) {
            queue.markFailed(request.uid, e.getMessage());
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
}
