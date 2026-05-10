package integration.java8;

public class AiaRobotActionRunner {
    private final AiaServerConnector connector;
    private final AiaRobotActionAdapter adapter;
    private final AiaDecisionParser parser;

    public AiaRobotActionRunner(AiaServerConnector connector, AiaRobotActionAdapter adapter) {
        if (connector == null) {
            throw new IllegalArgumentException("AiaServerConnector is required");
        }
        if (adapter == null) {
            throw new IllegalArgumentException("AiaRobotActionAdapter is required");
        }
        this.connector = connector;
        this.adapter = adapter;
        this.parser = new AiaDecisionParser();
    }

    public AiaDecision tick(Object robot) {
        try {
            String json = adapter.buildOpsTickJson(robot);
            String response = connector.opsTick(json);
            AiaDecision decision = parser.parseOpsTick(response);
            execute(robot, decision);
            return decision;
        } catch (Exception error) {
            handleError(robot, error);
            return parser.fallback(error.getMessage() == null ? "java_action_runner_error" : error.getMessage());
        }
    }

    public void execute(Object robot, AiaDecision decision) throws Exception {
        if (decision == null) {
            adapter.idle(robot);
            return;
        }
        if (!adapter.canExecute(robot, decision)) {
            adapter.idle(robot);
            return;
        }

        String action = normalize(decision.getAction());
        if ("MOVE".equals(action)) {
            adapter.move(robot, decision);
            return;
        }
        if ("ATTACK".equals(action)) {
            adapter.attack(robot, decision);
            return;
        }
        if ("USE_SKILL".equals(action)) {
            adapter.useSkill(robot, decision);
            return;
        }
        if ("RETREAT".equals(action)) {
            adapter.retreat(robot, decision);
            return;
        }
        if ("PICKUP".equals(action)) {
            adapter.pickup(robot, decision);
            return;
        }
        adapter.idle(robot);
    }

    private void handleError(Object robot, Exception error) {
        try {
            adapter.onError(robot, error);
        } catch (Exception ignored) {
            try {
                adapter.idle(robot);
            } catch (Exception ignoredAgain) {
                // The game server should never crash only because AIA action execution failed.
            }
        }
    }

    private String normalize(String action) {
        if (action == null) {
            return "IDLE";
        }
        return action.trim().toUpperCase();
    }
}
