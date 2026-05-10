package integration.java8;

public interface AiaRobotActionAdapter {
    /**
     * Build the /api/v1/robot/ops-tick JSON body from the server robot object.
     * The robot object type is intentionally Object so every game server can use its own class.
     */
    String buildOpsTickJson(Object robot) throws Exception;

    /**
     * Server-side safety gate. Return false when the action must not be executed.
     */
    boolean canExecute(Object robot, AiaDecision decision) throws Exception;

    void move(Object robot, AiaDecision decision) throws Exception;

    void attack(Object robot, AiaDecision decision) throws Exception;

    void useSkill(Object robot, AiaDecision decision) throws Exception;

    void retreat(Object robot, AiaDecision decision) throws Exception;

    void pickup(Object robot, AiaDecision decision) throws Exception;

    void idle(Object robot) throws Exception;

    /**
     * Called when AIA call, parsing, validation, or execution fails.
     * Implementations usually log the error and fall back to idle or the server's old AI.
     */
    void onError(Object robot, Exception error) throws Exception;
}
