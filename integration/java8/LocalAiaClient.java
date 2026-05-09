package integration.java8;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.lang.reflect.Field;
import java.net.HttpURLConnection;
import java.net.ProtocolException;
import java.net.URL;
import java.net.URLEncoder;

public class LocalAiaClient {
    private final String baseUrl;
    private final String apiKey;
    private int connectTimeoutMs = 3000;
    private int readTimeoutMs = 5000;

    public LocalAiaClient(String baseUrl, String apiKey) {
        this.baseUrl = trimTrailingSlash(baseUrl);
        this.apiKey = apiKey;
    }

    public void setTimeouts(int connectTimeoutMs, int readTimeoutMs) {
        this.connectTimeoutMs = Math.max(500, connectTimeoutMs);
        this.readTimeoutMs = Math.max(500, readTimeoutMs);
    }

    public String getJson(String path) throws IOException {
        return requestJson("GET", path, null);
    }

    public String postJson(String path, String json) throws IOException {
        return requestJson("POST", path, json);
    }

    public String putJson(String path, String json) throws IOException {
        return requestJson("PUT", path, json);
    }

    public String patchJson(String path, String json) throws IOException {
        return requestJson("PATCH", path, json);
    }

    public String deleteJson(String path) throws IOException {
        return requestJson("DELETE", path, null);
    }

    public String requestJson(String method, String path, String json) throws IOException {
        HttpURLConnection conn = null;
        try {
            URL url = new URL(baseUrl + path);
            conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(connectTimeoutMs);
            conn.setReadTimeout(readTimeoutMs);
            setRequestMethod(conn, method);
            conn.setRequestProperty("Accept", "application/json");
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            if (apiKey != null && apiKey.length() > 0) {
                conn.setRequestProperty("X-API-Key", apiKey);
            }

            if (json != null) {
                conn.setDoOutput(true);
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(json.getBytes("UTF-8"));
                }
            }

            int code = conn.getResponseCode();
            InputStream stream = code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream();
            String body = readBody(stream);
            if (code < 200 || code >= 300) {
                throw new IOException("AIA HTTP " + code + " " + method + " " + path + " body=" + body);
            }
            return body;
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }

    public boolean healthCheck() {
        try {
            getJson("/health");
            return true;
        } catch (Exception ignored) {
            return false;
        }
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

    public String listRobots() throws IOException {
        return getJson("/robot");
    }

    public String createRobotProfile(String json) throws IOException {
        return postJson("/robot/profile", json);
    }

    public String replaceRobotProfile(String agentId, String json) throws IOException {
        return putJson("/robot/" + encodePathSegment(agentId) + "/profile", json);
    }

    public String patchRobotProfile(String agentId, String json) throws IOException {
        return patchJson("/robot/" + encodePathSegment(agentId) + "/profile", json);
    }

    public String getRobot(String agentId) throws IOException {
        return getJson("/robot/" + encodePathSegment(agentId));
    }

    public String deleteRobot(String agentId) throws IOException {
        return deleteJson("/robot/" + encodePathSegment(agentId));
    }

    private String readBody(InputStream stream) throws IOException {
        if (stream == null) {
            return "";
        }
        BufferedReader reader = new BufferedReader(new InputStreamReader(stream, "UTF-8"));
        try {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
            return sb.toString();
        } finally {
            reader.close();
        }
    }

    private void setRequestMethod(HttpURLConnection conn, String method) throws IOException {
        try {
            conn.setRequestMethod(method);
        } catch (ProtocolException e) {
            if (!"PATCH".equals(method)) {
                throw e;
            }
            forcePatchMethod(conn, e);
        }
    }

    private void forcePatchMethod(HttpURLConnection conn, ProtocolException original) throws IOException {
        try {
            Field methodField = HttpURLConnection.class.getDeclaredField("method");
            methodField.setAccessible(true);
            methodField.set(conn, "PATCH");
        } catch (Exception reflectionError) {
            throw original;
        }
    }

    private String encodePathSegment(String value) throws IOException {
        if (value == null) {
            return "";
        }
        return URLEncoder.encode(value, "UTF-8").replace("+", "%20");
    }

    private String trimTrailingSlash(String value) {
        if (value == null || value.length() == 0) {
            return "http://127.0.0.1:8000";
        }
        while (value.endsWith("/")) {
            value = value.substring(0, value.length() - 1);
        }
        return value;
    }
}
