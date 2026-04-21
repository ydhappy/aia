# Java 8 연동 예시

아래 예시는 Java 8 서버에서 AI 브리지 서버의 `/decide` 엔드포인트를 호출하는 간단한 방식입니다.

## 개요
- Java 8 서버가 게임 상태를 JSON으로 만듭니다.
- `POST /decide` 로 전송합니다.
- 응답받은 액션을 서버에서 다시 검증한 후 실행합니다.

## HttpURLConnection 예시
```java
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class AiaClient {

    public static String decide() throws Exception {
        URL url = new URL("http://127.0.0.1:8000/decide");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
        conn.setDoOutput(true);
        conn.setConnectTimeout(2000);
        conn.setReadTimeout(2000);

        String json = "{"
                + "\"agent_id\":\"bot_001\"," 
                + "\"tick\":101,"
                + "\"state\":{"
                + "\"hp\":45,"
                + "\"mp\":20,"
                + "\"x\":100,"
                + "\"y\":200,"
                + "\"target_id\":\"mob_1\","
                + "\"target_distance\":1,"
                + "\"is_under_attack\":true,"
                + "\"cooldowns\":{\"heal\":0},"
                + "\"inventory\":{\"potion\":2},"
                + "\"extras\":{}"
                + "}"
                + "}";

        try (OutputStream os = conn.getOutputStream()) {
            byte[] input = json.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        StringBuilder response = new StringBuilder();
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = br.readLine()) != null) {
                response.append(line.trim());
            }
        }

        return response.toString();
    }
}
```

## 서버 측 주의사항
- AI 응답을 그대로 실행하지 말고 서버에서 유효성 검사를 먼저 수행합니다.
- 허용 액션만 실행합니다.
- 타겟 존재 여부, 좌표, 쿨다운, 안전 구역 여부를 다시 확인합니다.
- 타임아웃 시 기본 액션(`IDLE` 또는 `RETREAT`)으로 폴백합니다.

## 권장 운영 방식
- 평상시 행동은 규칙 엔진 위주
- LLM은 예외 상황 또는 대화형 기능에 한정
- Java 8 서버는 항상 최종 실행 권한을 보유
