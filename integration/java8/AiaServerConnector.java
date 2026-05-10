package integration.java8;

public class AiaServerConnector {
    private final AiaServerConfig config;
    private final AiaRobotSpawnAdapter spawnAdapter;
    private final LocalAiaClient aiaClient;

    public AiaServerConnector(AiaServerConfig config, AiaRobotSpawnAdapter spawnAdapter) {
        if (config == null) {
            throw new IllegalArgumentException("AiaServerConfig is required");
        }
        if (spawnAdapter == null) {
            throw new IllegalArgumentException("AiaRobotSpawnAdapter is required");
        }
        config.validate();
        this.config = config;
        this.spawnAdapter = spawnAdapter;
        this.aiaClient = new LocalAiaClient(config.getAiaBaseUrl(), config.getApiKey());
        this.aiaClient.setTimeouts(config.getConnectTimeoutMs(), config.getReadTimeoutMs());
    }

    public LocalAiaClient getAiaClient() {
        return aiaClient;
    }

    public boolean isAiaAlive() {
        return aiaClient.healthCheck();
    }

    public int bootSpawnOnce() throws Exception {
        if (config.isHealthCheckBeforeSpawn() && !aiaClient.healthCheck()) {
            throw new IllegalStateException("AIA health check failed: " + config.getAiaBaseUrl());
        }
        AiaRobotSpawnPoller poller = new AiaRobotSpawnPoller(
                config.getJdbcUrl(),
                config.getDbUser(),
                config.getDbPassword(),
                config.getServerName(),
                aiaClient,
                spawnAdapter
        );
        poller.setBatchSize(config.getSpawnBatchSize());
        return poller.runOnce();
    }

    public String opsTick(String json) throws Exception {
        return aiaClient.opsTick(json);
    }

    public String decide(String json) throws Exception {
        return aiaClient.decide(json);
    }

    public String sync(String json) throws Exception {
        return aiaClient.sync(json);
    }

    public String feedback(String json) throws Exception {
        return aiaClient.feedback(json);
    }

    public String listRobots() throws Exception {
        return aiaClient.listRobots();
    }

    public String createProfile(String json) throws Exception {
        return aiaClient.createRobotProfile(json);
    }

    public static AiaServerConnector createDefault(
            String jdbcUrl,
            String dbUser,
            String dbPassword,
            String serverName,
            AiaRobotSpawnAdapter adapter
    ) {
        AiaServerConfig config = new AiaServerConfig()
                .setJdbcUrl(jdbcUrl)
                .setDbUser(dbUser)
                .setDbPassword(dbPassword)
                .setServerName(serverName);
        return new AiaServerConnector(config, adapter);
    }
}
