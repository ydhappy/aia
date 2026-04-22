package integration.java8;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class LocalAiaClient {
    private final String baseUrl;
    private final String apiKey;

    public LocalAiaClient(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    public String postJson(String path, String json) throws IOException {
        URL url = new URL(baseUrl + path);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
        conn.setRequestProperty("X-API-Key", apiKey);
        conn.setDoOutput(true);

        try (OutputStream os = conn.getOutputStream()) {
            os.write(json.getBytes("UTF-8"));
        }

        int code = conn.getResponseCode();
        BufferedReader reader = new BufferedReader(new InputStreamReader(
                code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream(),
                "UTF-8"
        ));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line);
        }
        reader.close();
        return sb.toString();
    }

    public String decide(String json) throws IOException {
        return postJson("/decide", json);
    }

    public String sync(String json) throws IOException {
        return postJson("/api/v1/robot/sync", json);
    }

    public String opsTick(String json) throws IOException {
        return postJson("/api/v1/robot/ops-tick", json);
    }

    public String feedback(String json) throws IOException {
        return postJson("/robot/feedback", json);
    }
}
