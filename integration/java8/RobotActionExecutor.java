package integration.java8;

/**
 * AIA가 반환한 action을 실제 게임서버 동작으로 연결하는 클래스입니다.
 *
 * 초보자용 설명:
 * - 처음에는 println으로 테스트하세요.
 * - 그 다음 TODO 부분을 서버 기존 이동/공격/스킬 함수로 바꾸세요.
 * - AIA는 결정만 하고, 실제 실행은 반드시 서버가 최종 검증 후 수행해야 합니다.
 */
public class RobotActionExecutor {

    public static class ExecutionResult {
        public boolean success;
        public String outcome;
        public String detail;

        public ExecutionResult(boolean success, String outcome, String detail) {
            this.success = success;
            this.outcome = outcome;
            this.detail = detail;
        }
    }

    public ExecutionResult execute(Object serverRobotObject, AiaDecision decision) {
        if (decision == null) {
            return new ExecutionResult(false, "failure", "decision_null");
        }

        String action = decision.getAction();
        if ("MOVE".equals(action)) {
            return doMove(serverRobotObject, decision);
        }
        if ("ATTACK".equals(action)) {
            return doAttack(serverRobotObject, decision);
        }
        if ("USE_SKILL".equals(action)) {
            return doSkill(serverRobotObject, decision);
        }
        if ("RETREAT".equals(action)) {
            return doRetreat(serverRobotObject, decision);
        }
        if ("PICKUP".equals(action)) {
            return doPickup(serverRobotObject, decision);
        }
        return doIdle(serverRobotObject, decision);
    }

    private ExecutionResult doMove(Object serverRobotObject, AiaDecision decision) {
        // TODO: 현재 서버의 이동 가능 여부 검증 후 기존 이동 함수로 연결하세요.
        System.out.println("[AIA][MOVE] " + decision);
        return new ExecutionResult(true, "success", "move_placeholder_executed");
    }

    private ExecutionResult doAttack(Object serverRobotObject, AiaDecision decision) {
        // TODO: 현재 서버의 타겟 유효성 확인 후 기존 공격 함수로 연결하세요.
        System.out.println("[AIA][ATTACK] " + decision);
        return new ExecutionResult(true, "success", "attack_placeholder_executed");
    }

    private ExecutionResult doSkill(Object serverRobotObject, AiaDecision decision) {
        // TODO: 현재 서버의 스킬 사용 가능 여부/쿨타임 확인 후 기존 스킬 함수로 연결하세요.
        System.out.println("[AIA][USE_SKILL] " + decision);
        return new ExecutionResult(true, "success", "skill_placeholder_executed");
    }

    private ExecutionResult doRetreat(Object serverRobotObject, AiaDecision decision) {
        // TODO: 현재 서버의 귀환/텔레포트/안전지대 이동 함수로 연결하세요.
        System.out.println("[AIA][RETREAT] " + decision);
        return new ExecutionResult(true, "success", "retreat_placeholder_executed");
    }

    private ExecutionResult doPickup(Object serverRobotObject, AiaDecision decision) {
        // TODO: 현재 서버의 아이템 줍기 함수로 연결하세요.
        System.out.println("[AIA][PICKUP] " + decision);
        return new ExecutionResult(true, "success", "pickup_placeholder_executed");
    }

    private ExecutionResult doIdle(Object serverRobotObject, AiaDecision decision) {
        System.out.println("[AIA][IDLE] " + decision);
        return new ExecutionResult(true, "success", "idle_placeholder_executed");
    }
}
