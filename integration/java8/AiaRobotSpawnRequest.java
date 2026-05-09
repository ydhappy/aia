package integration.java8;

import java.sql.ResultSet;
import java.sql.SQLException;

public class AiaRobotSpawnRequest {
    public long uid;
    public String requestId;
    public String serverName;
    public String agentId;
    public String name;
    public String classType;
    public int classId;
    public int level;
    public int locX;
    public int locY;
    public int locMap;
    public int heading;
    public String role;
    public String style;
    public int homeX;
    public int homeY;
    public int homeMap;
    public String huntZoneId;
    public int priority;
    public String metadataJson;

    public static AiaRobotSpawnRequest from(ResultSet rs) throws SQLException {
        AiaRobotSpawnRequest request = new AiaRobotSpawnRequest();
        request.uid = rs.getLong("uid");
        request.requestId = rs.getString("request_id");
        request.serverName = rs.getString("server_name");
        request.agentId = rs.getString("agent_id");
        request.name = rs.getString("name");
        request.classType = rs.getString("class_type");
        request.classId = rs.getInt("class_id");
        request.level = rs.getInt("level");
        request.locX = rs.getInt("loc_x");
        request.locY = rs.getInt("loc_y");
        request.locMap = rs.getInt("loc_map");
        request.heading = rs.getInt("heading");
        request.role = rs.getString("role");
        request.style = rs.getString("style");
        request.homeX = rs.getInt("home_x");
        request.homeY = rs.getInt("home_y");
        request.homeMap = rs.getInt("home_map");
        request.huntZoneId = rs.getString("hunt_zone_id");
        request.priority = rs.getInt("priority");
        request.metadataJson = rs.getString("metadata_json");
        return request;
    }

    public String toAiaProfileJson() {
        String safeName = json(name);
        String safeAgentId = json(agentId);
        String safeRole = json(role == null || role.length() == 0 ? "custom" : role);
        String safeStyle = json(style == null || style.length() == 0 ? "balanced" : style);
        String safeClassType = json(classType);
        String safeServer = json(serverName);
        String safeHuntZone = json(huntZoneId);
        String metadata = metadataJson;
        if (metadata == null || metadata.trim().length() == 0) {
            metadata = "{}";
        }
        return "{"
                + "\"agent_id\":\"" + safeAgentId + "\","
                + "\"name\":\"" + safeName + "\","
                + "\"role\":\"" + safeRole + "\","
                + "\"style\":\"" + safeStyle + "\","
                + "\"home_x\":" + homeX + ","
                + "\"home_y\":" + homeY + ","
                + "\"metadata\":{"
                + "\"source\":\"aia_spawn_request\","
                + "\"server_name\":\"" + safeServer + "\","
                + "\"class_type\":\"" + safeClassType + "\","
                + "\"class_id\":" + classId + ","
                + "\"level\":" + level + ","
                + "\"loc_map\":" + locMap + ","
                + "\"home_map\":" + homeMap + ","
                + "\"hunt_zone_id\":\"" + safeHuntZone + "\","
                + "\"raw\":" + metadata
                + "}"
                + "}";
    }

    private static String json(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r", "\\r").replace("\n", "\\n");
    }
}
