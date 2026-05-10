package integration.java8;

public class AiaServerConfig {
    private String aiaBaseUrl = "http://127.0.0.1:8000";
    private String apiKey = "";
    private String jdbcUrl = "jdbc:mysql://127.0.0.1:3306/your_game_db?useUnicode=true&characterEncoding=utf8";
    private String dbUser = "root";
    private String dbPassword = "";
    private String serverName = "main";
    private int spawnBatchSize = 20;
    private int connectTimeoutMs = 3000;
    private int readTimeoutMs = 5000;
    private boolean healthCheckBeforeSpawn = true;

    public String getAiaBaseUrl() {
        return aiaBaseUrl;
    }

    public AiaServerConfig setAiaBaseUrl(String aiaBaseUrl) {
        this.aiaBaseUrl = aiaBaseUrl;
        return this;
    }

    public String getApiKey() {
        return apiKey;
    }

    public AiaServerConfig setApiKey(String apiKey) {
        this.apiKey = apiKey;
        return this;
    }

    public String getJdbcUrl() {
        return jdbcUrl;
    }

    public AiaServerConfig setJdbcUrl(String jdbcUrl) {
        this.jdbcUrl = jdbcUrl;
        return this;
    }

    public String getDbUser() {
        return dbUser;
    }

    public AiaServerConfig setDbUser(String dbUser) {
        this.dbUser = dbUser;
        return this;
    }

    public String getDbPassword() {
        return dbPassword;
    }

    public AiaServerConfig setDbPassword(String dbPassword) {
        this.dbPassword = dbPassword;
        return this;
    }

    public String getServerName() {
        return serverName;
    }

    public AiaServerConfig setServerName(String serverName) {
        this.serverName = serverName;
        return this;
    }

    public int getSpawnBatchSize() {
        return spawnBatchSize;
    }

    public AiaServerConfig setSpawnBatchSize(int spawnBatchSize) {
        this.spawnBatchSize = spawnBatchSize;
        return this;
    }

    public int getConnectTimeoutMs() {
        return connectTimeoutMs;
    }

    public AiaServerConfig setConnectTimeoutMs(int connectTimeoutMs) {
        this.connectTimeoutMs = connectTimeoutMs;
        return this;
    }

    public int getReadTimeoutMs() {
        return readTimeoutMs;
    }

    public AiaServerConfig setReadTimeoutMs(int readTimeoutMs) {
        this.readTimeoutMs = readTimeoutMs;
        return this;
    }

    public boolean isHealthCheckBeforeSpawn() {
        return healthCheckBeforeSpawn;
    }

    public AiaServerConfig setHealthCheckBeforeSpawn(boolean healthCheckBeforeSpawn) {
        this.healthCheckBeforeSpawn = healthCheckBeforeSpawn;
        return this;
    }

    public void validate() {
        if (jdbcUrl == null || jdbcUrl.length() == 0) {
            throw new IllegalArgumentException("AIA jdbcUrl is required");
        }
        if (dbUser == null) {
            throw new IllegalArgumentException("AIA dbUser is required");
        }
        if (serverName == null || serverName.trim().length() == 0) {
            throw new IllegalArgumentException("AIA serverName is required");
        }
    }
}
