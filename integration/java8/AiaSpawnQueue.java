package integration.java8;

import java.util.List;

public interface AiaSpawnQueue {
    /**
     * Claim pending spawn requests for one server.
     * Implementations may use MySQL, MariaDB, MSSQL, PostgreSQL, SQLite, files, or HTTP.
     */
    List<AiaRobotSpawnRequest> claimPending(String serverName, int batchSize) throws Exception;

    /**
     * Mark a claimed request as completed.
     */
    void markDone(long uid, long serverObjectId, String message) throws Exception;

    /**
     * Mark a claimed request as failed.
     */
    void markFailed(long uid, String error) throws Exception;
}
