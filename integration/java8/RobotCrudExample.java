package integration.java8;

public class RobotCrudExample {
    public static void main(String[] args) throws Exception {
        LocalAiaClient aia = new LocalAiaClient("http://127.0.0.1:8000", "");
        String agentId = "java8_robot_1";

        String createProfileJson = "{"
                + "\"agent_id\":\"" + agentId + "\","
                + "\"name\":\"자바8로봇\","
                + "\"role\":\"custom\","
                + "\"style\":\"balanced\","
                + "\"metadata\":{\"source\":\"java8\",\"memo\":\"UTF-8 테스트\"}"
                + "}";

        System.out.println("CREATE: " + aia.createRobotProfile(createProfileJson));
        System.out.println("LIST: " + aia.listRobots());
        System.out.println("READ: " + aia.getRobot(agentId));

        String patchProfileJson = "{"
                + "\"style\":\"defensive\","
                + "\"metadata\":{\"source\":\"java8\",\"memo\":\"수정 완료\"}"
                + "}";

        System.out.println("PATCH: " + aia.patchRobotProfile(agentId, patchProfileJson));
        System.out.println("READ_AFTER_PATCH: " + aia.getRobot(agentId));
        System.out.println("DELETE: " + aia.deleteRobot(agentId));
    }
}
