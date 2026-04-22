package integration.java8;

/**
 * 외부 JSON 라이브러리 없이 최소한으로 AIA 응답을 파싱하는 클래스입니다.
 *
 * 중요:
 * - 초보자는 처음부터 완벽한 JSON 파서를 만들 필요가 없습니다.
 * - 이 클래스는 AIA 기본 응답 구조(action/confidence/reason/source/action_args)에 맞춘 단순 파서입니다.
 * - 더 안정적으로 쓰려면 나중에 Jackson/Gson으로 교체해도 됩니다.
 */
public class AiaDecisionParser {
    private static final String EMPTY_JSON_OBJECT = "{}";

    public AiaDecision parse(String json) {
        if (json == null || json.trim().isEmpty()) {
            return fallback("empty_response");
        }

        String action = readString(json, "action", "IDLE");
        String reason = readString(json, "reason", "missing_reason");
        String source = readString(json, "source", "unknown");
        double confidence = readDouble(json, "confidence", 0.0d);
        String actionArgsJson = readObject(json, "action_args", EMPTY_JSON_OBJECT);

        return new AiaDecision(action, actionArgsJson, confidence, reason, source);
    }

    public AiaDecision parseOpsTick(String json) {
        String decideResultJson = readObject(json, "decide_result", "");
        if (decideResultJson.length() > 0 && !"null".equals(decideResultJson)) {
            return parse(decideResultJson);
        }
        return parse(json);
    }

    public AiaDecision fallback(String reason) {
        return new AiaDecision("IDLE", EMPTY_JSON_OBJECT, 0.0d, reason, "java_fallback");
    }

    private String readString(String json, String key, String defaultValue) {
        String marker = "\"" + key + "\"";
        int start = json.indexOf(marker);
        if (start < 0) {
            return defaultValue;
        }
        int colon = json.indexOf(':', start);
        if (colon < 0) {
            return defaultValue;
        }
        int firstQuote = json.indexOf('"', colon + 1);
        if (firstQuote < 0) {
            return defaultValue;
        }
        int secondQuote = json.indexOf('"', firstQuote + 1);
        if (secondQuote < 0) {
            return defaultValue;
        }
        return json.substring(firstQuote + 1, secondQuote);
    }

    private double readDouble(String json, String key, double defaultValue) {
        String marker = "\"" + key + "\"";
        int start = json.indexOf(marker);
        if (start < 0) {
            return defaultValue;
        }
        int colon = json.indexOf(':', start);
        if (colon < 0) {
            return defaultValue;
        }
        int end = colon + 1;
        while (end < json.length() && " \t\r\n".indexOf(json.charAt(end)) >= 0) {
            end++;
        }
        int tail = end;
        while (tail < json.length() && "0123456789.-".indexOf(json.charAt(tail)) >= 0) {
            tail++;
        }
        try {
            return Double.parseDouble(json.substring(end, tail));
        } catch (Exception ignore) {
            return defaultValue;
        }
    }

    private String readObject(String json, String key, String defaultValue) {
        String marker = "\"" + key + "\"";
        int start = json.indexOf(marker);
        if (start < 0) {
            return defaultValue;
        }
        int colon = json.indexOf(':', start);
        if (colon < 0) {
            return defaultValue;
        }
        int braceStart = colon + 1;
        while (braceStart < json.length() && " \t\r\n".indexOf(json.charAt(braceStart)) >= 0) {
            braceStart++;
        }
        if (braceStart >= json.length() || json.charAt(braceStart) != '{') {
            return defaultValue;
        }
        int depth = 0;
        for (int i = braceStart; i < json.length(); i++) {
            char c = json.charAt(i);
            if (c == '{') {
                depth++;
            }
            if (c == '}') {
                depth--;
            }
            if (depth == 0) {
                return json.substring(braceStart, i + 1);
            }
        }
        return defaultValue;
    }
}
