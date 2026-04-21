package integration.java8;

/**
 * AIA가 반환한 action 한 건을 담는 최소 모델입니다.
 *
 * 초보자용 설명:
 * - action: MOVE / ATTACK / USE_SKILL / RETREAT / PICKUP / IDLE
 * - actionArgsJson: action_args 전체를 문자열 그대로 보관
 * - confidence: 신뢰도
 * - reason: 판단 이유
 * - source: rule_engine, fallback 등
 */
public class AiaDecision {
    private final String action;
    private final String actionArgsJson;
    private final double confidence;
    private final String reason;
    private final String source;

    public AiaDecision(String action, String actionArgsJson, double confidence, String reason, String source) {
        this.action = action;
        this.actionArgsJson = actionArgsJson;
        this.confidence = confidence;
        this.reason = reason;
        this.source = source;
    }

    public String getAction() {
        return action;
    }

    public String getActionArgsJson() {
        return actionArgsJson;
    }

    public double getConfidence() {
        return confidence;
    }

    public String getReason() {
        return reason;
    }

    public String getSource() {
        return source;
    }

    @Override
    public String toString() {
        return "AiaDecision{" +
                "action='" + action + '\'' +
                ", actionArgsJson='" + actionArgsJson + '\'' +
                ", confidence=" + confidence +
                ", reason='" + reason + '\'' +
                ", source='" + source + '\'' +
                '}';
    }
}
