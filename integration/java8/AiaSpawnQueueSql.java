package integration.java8;

public class AiaSpawnQueueSql {
    private final String dialect;

    private AiaSpawnQueueSql(String dialect) {
        this.dialect = dialect == null ? "mysql" : dialect.toLowerCase();
    }

    public static AiaSpawnQueueSql forDialect(String dialect) {
        return new AiaSpawnQueueSql(dialect);
    }

    public static AiaSpawnQueueSql forJdbcUrl(String jdbcUrl) {
        String lower = jdbcUrl == null ? "" : jdbcUrl.toLowerCase();
        if (lower.startsWith("jdbc:sqlserver:")) {
            return new AiaSpawnQueueSql("mssql");
        }
        if (lower.startsWith("jdbc:postgresql:")) {
            return new AiaSpawnQueueSql("postgresql");
        }
        if (lower.startsWith("jdbc:sqlite:")) {
            return new AiaSpawnQueueSql("sqlite");
        }
        return new AiaSpawnQueueSql("mysql");
    }

    public String selectPendingSql() {
        if ("mssql".equals(dialect)) {
            return "SELECT TOP (?) uid FROM aia_robot_spawn_request "
                    + "WHERE status = 'pending' AND server_name = ? "
                    + "ORDER BY priority DESC, uid ASC";
        }
        if ("postgresql".equals(dialect)) {
            return "SELECT uid FROM aia_robot_spawn_request "
                    + "WHERE status = 'pending' AND server_name = ? "
                    + "ORDER BY priority DESC, uid ASC LIMIT ?";
        }
        if ("sqlite".equals(dialect)) {
            return "SELECT uid FROM aia_robot_spawn_request "
                    + "WHERE status = 'pending' AND server_name = ? "
                    + "ORDER BY priority DESC, uid ASC LIMIT ?";
        }
        return "SELECT uid FROM aia_robot_spawn_request "
                + "WHERE status = 'pending' AND server_name = ? "
                + "ORDER BY priority DESC, uid ASC LIMIT ?";
    }

    public String claimOneSql() {
        if ("mssql".equals(dialect)) {
            return "UPDATE aia_robot_spawn_request "
                    + "SET status = 'claimed', attempts = attempts + 1, claimed_at = CURRENT_TIMESTAMP "
                    + "WHERE uid = ? AND status = 'pending'";
        }
        if ("postgresql".equals(dialect)) {
            return "UPDATE aia_robot_spawn_request "
                    + "SET status = 'claimed', attempts = attempts + 1, claimed_at = CURRENT_TIMESTAMP "
                    + "WHERE uid = ? AND status = 'pending'";
        }
        if ("sqlite".equals(dialect)) {
            return "UPDATE aia_robot_spawn_request "
                    + "SET status = 'claimed', attempts = attempts + 1, claimed_at = CURRENT_TIMESTAMP "
                    + "WHERE uid = ? AND status = 'pending'";
        }
        return "UPDATE aia_robot_spawn_request "
                + "SET status = 'claimed', attempts = attempts + 1, claimed_at = NOW() "
                + "WHERE uid = ? AND status = 'pending'";
    }

    public String fetchClaimedSql() {
        return "SELECT * FROM aia_robot_spawn_request "
                + "WHERE uid = ? AND status = 'claimed' AND server_name = ?";
    }

    public String markDoneSql() {
        if ("mysql".equals(dialect)) {
            return "UPDATE aia_robot_spawn_request "
                    + "SET status = 'done', done_at = NOW(), last_error = ? "
                    + "WHERE uid = ?";
        }
        return "UPDATE aia_robot_spawn_request "
                + "SET status = 'done', done_at = CURRENT_TIMESTAMP, last_error = ? "
                + "WHERE uid = ?";
    }

    public String markFailedSql() {
        return "UPDATE aia_robot_spawn_request "
                + "SET status = 'failed', last_error = ? "
                + "WHERE uid = ?";
    }

    public boolean usesTopLimit() {
        return "mssql".equals(dialect);
    }

    public String getDialect() {
        return dialect;
    }
}
