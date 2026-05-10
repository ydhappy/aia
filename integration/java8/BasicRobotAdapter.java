package integration.java8;

/**
 * Basic adapter for servers that do not have robot tables yet.
 *
 * This adapter writes to sql/robot_min_mysql55.sql tables only.
 * It does not automatically register a live in-memory game object into your server World.
 * After this works, replace or extend createAndSpawn() to create your real server robot object,
 * add it to World, and register it to the server AI scheduler.
 */
public class BasicRobotAdapter implements AiaRobotSpawnAdapter {
    private final RobotStore store;
    private final AiaRobotTemplateConfig template;
    private final ObjectIdProvider objectIdProvider;

    public BasicRobotAdapter(RobotStore store, AiaRobotTemplateConfig template, ObjectIdProvider objectIdProvider) {
        if (store == null) {
            throw new IllegalArgumentException("RobotStore is required");
        }
        if (template == null) {
            throw new IllegalArgumentException("AiaRobotTemplateConfig is required");
        }
        if (objectIdProvider == null) {
            throw new IllegalArgumentException("ObjectIdProvider is required");
        }
        this.store = store;
        this.template = template;
        this.objectIdProvider = objectIdProvider;
    }

    public boolean exists(AiaRobotSpawnRequest request) throws Exception {
        if (request == null) {
            return true;
        }
        return store.existsByAgentIdOrName(request.agentId, request.name);
    }

    public long createAndSpawn(AiaRobotSpawnRequest request) throws Exception {
        long objectId = objectIdProvider.nextObjectId();
        long robotUid = store.createRobot(request, template, objectId);
        afterCreateRows(request, robotUid, objectId);
        return objectId;
    }

    public void afterSpawn(AiaRobotSpawnRequest request, long serverObjectId) throws Exception {
        // Hook for logging or broadcast.
    }

    protected void afterCreateRows(AiaRobotSpawnRequest request, long robotUid, long objectId) throws Exception {
        // Override this method in your game server to:
        // 1. Create the actual in-memory robot object.
        // 2. Set x/y/map/heading/class/level from request.
        // 3. Register it to World.
        // 4. Register it to the server AI scheduler.
    }

    public interface ObjectIdProvider {
        long nextObjectId() throws Exception;
    }
}
