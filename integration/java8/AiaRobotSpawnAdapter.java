package integration.java8;

public interface AiaRobotSpawnAdapter {
    /**
     * Return true when a robot with the same agent_id or name already exists in the running server.
     */
    boolean exists(AiaRobotSpawnRequest request) throws Exception;

    /**
     * Create the real server robot using the server's own IdFactory, DB insert, inventory, skills, and world spawn logic.
     * Return the server object id or robot uid created by the game server.
     */
    long createAndSpawn(AiaRobotSpawnRequest request) throws Exception;

    /**
     * Called after the server robot has been created. Use it to log, broadcast, or attach custom AI state.
     */
    void afterSpawn(AiaRobotSpawnRequest request, long serverObjectId) throws Exception;
}
