package integration.java8;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

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

    public static AiaServerConfig fromFile(String path) throws IOException {
        if (path == null || path.trim().length() == 0) {
            throw new IllegalArgumentException("AIA config file path is required");
        }
        FileInputStream in = new FileInputStream(path);
        try {
            return fromProperties(in);
        } finally {
            in.close();
        }
    }

    public static AiaServerConfig fromProperties(InputStream input) throws IOException {
        if (input == null) {
            throw new IllegalArgumentException("AIA config input is required");
        }
        Properties props = new Properties();
        props.load(input);
        return fromProperties(props);
    }

    public static AiaServerConfig fromProperties(Properties props) {
        AiaServerConfig config = new AiaServerConfig();
        if (props == null) {
            return config;
        }
        config.setAiaBaseUrl(text(props, "aia.baseUrl", config.getAiaBaseUrl()));
        config.setApiKey(text(props, "aia.apiKey", config.getApiKey()));
        config.setJdbcUrl(text(props, "aia.jdbcUrl", config.getJdbcUrl()));
        config.setDbUser(text(props, "aia.dbUser", config.getDbUser()));
        config.setDbPassword(text(props, "aia.dbPassword", config.getDbPassword()));
        config.setServerName(text(props, "aia.serverName", config.getServerName()));
        config.setSpawnBatchSize(number(props, "aia.spawnBatchSize", config.getSpawnBatchSize(), 1, 500));
        config.setConnectTimeoutMs(number(props, "aia.connectTimeoutMs", config.getConnectTimeoutMs(), 100, 60000));
        config.setReadTimeoutMs(number(props, "aia.readTimeoutMs", config.getReadTimeoutMs(), 100, 120000));
        config.setHealthCheckBeforeSpawn(flag(props, "aia.healthCheckBeforeSpawn", config.isHealthCheckBeforeSpawn()));
        config.validate();
        return config;
    }

    public String getAiaBaseUrl() {
        return aiaBaseUrl;
    }

    public AiaServerConfig setAiaBaseUrl(String aiaBaseUrl) {
        this.aiaBaseUrl = clean(aiaBaseUrl, "http://127.0.0.1:8000");
        return this;
    }

    public String getApiKey() {
        return apiKey;
    }

    public AiaServerConfig setApiKey(String apiKey) {
        this.apiKey = apiKey == null ? "" : apiKey.trim();
        return this;
    }

    public String getJdbcUrl() {
        return jdbcUrl;
    }

    public AiaServerConfig setJdbcUrl(String jdbcUrl) {
        this.jdbcUrl = clean(jdbcUrl, "");
        return this;
    }

    public String getDbUser() {
        return dbUser;
    }

    public AiaServerConfig setDbUser(String dbUser) {
        this.dbUser = clean(dbUser, "root");
        return this;
    }

    public String getDbPassword() {
        return dbPassword;
    }

    public AiaServerConfig setDbPassword(String dbPassword) {
        this.dbPassword = dbPassword == null ? "" : dbPassword;
        return this;
    }

    public String getServerName() {
        return serverName;
    }

    public AiaServerConfig setServerName(String serverName) {
        this.serverName = clean(serverName, "main");
        return this;
    }

    public int getSpawnBatchSize() {
        return spawnBatchSize;
    }

    public AiaServerConfig setSpawnBatchSize(int spawnBatchSize) {
        this.spawnBatchSize = clamp(spawnBatchSize, 1, 500, 20);
        return this;
    }

    public int getConnectTimeoutMs() {
        return connectTimeoutMs;
    }

    public AiaServerConfig setConnectTimeoutMs(int connectTimeoutMs) {
        this.connectTimeoutMs = clamp(connectTimeoutMs, 100, 60000, 3000);
        return this;
    }

    public int getReadTimeoutMs() {
        return readTimeoutMs;
    }

    public AiaServerConfig setReadTimeoutMs(int readTimeoutMs) {
        this.readTimeoutMs = clamp(readTimeoutMs, 100, 120000, 5000);
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
        if (aiaBaseUrl == null || aiaBaseUrl.trim().length() == 0) {
            throw new IllegalArgumentException("AIA baseUrl is required");
        }
        if (jdbcUrl == null || jdbcUrl.trim().length() == 0) {
            throw new IllegalArgumentException("AIA jdbcUrl is required");
        }
        if (dbUser == null || dbUser.trim().length() == 0) {
            throw new IllegalArgumentException("AIA dbUser is required");
        }
        if (serverName == null || serverName.trim().length() == 0) {
            throw new IllegalArgumentException("AIA serverName is required");
        }
    }

    private static String text(Properties props, String key, String fallback) {
        String value = props.getProperty(key);
        return value == null || value.trim().length() == 0 ? fallback : value.trim();
    }

    private static int number(Properties props, String key, int fallback, int min, int max) {
        String value = props.getProperty(key);
        if (value == null || value.trim().length() == 0) {
            return fallback;
        }
        try {
            return clamp(Integer.parseInt(value.trim()), min, max, fallback);
        } catch (Exception e) {
            return fallback;
        }
    }

    private static boolean flag(Properties props, String key, boolean fallback) {
        String value = props.getProperty(key);
        if (value == null || value.trim().length() == 0) {
            return fallback;
        }
        String clean = value.trim().toLowerCase();
        return "true".equals(clean) || "1".equals(clean) || "yes".equals(clean) || "y".equals(clean);
    }

    private static String clean(String value, String fallback) {
        if (value == null || value.trim().length() == 0) {
            return fallback;
        }
        return value.trim();
    }

    private static int clamp(int value, int min, int max, int fallback) {
        if (value < min || value > max) {
            return fallback;
        }
        return value;
    }
}
