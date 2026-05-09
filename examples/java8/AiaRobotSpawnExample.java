package integration.java8;

public class AiaRobotSpawnExample {
    public static void main(String[] args) throws Exception {
        String jdbcUrl = "jdbc:mysql://127.0.0.1:3306/your_game_db?useUnicode=true&characterEncoding=utf8";
        String dbUser = "root";
        String dbPassword = "root";
        String serverName = "main";

        LocalAiaClient aia = new LocalAiaClient("http://127.0.0.1:8000", "");
        AiaRobotSpawnAdapter adapter = new ExampleServerRobotAdapter();

        AiaRobotSpawnPoller poller = new AiaRobotSpawnPoller(
                jdbcUrl,
                dbUser,
                dbPassword,
                serverName,
                aia,
                adapter
        );
        poller.setBatchSize(20);

        int processed = poller.runOnce();
        System.out.println("AIA_ROBOT_SPAWN_PROCESSED=" + processed);
    }

    static class ExampleServerRobotAdapter implements AiaRobotSpawnAdapter {
        public boolean exists(AiaRobotSpawnRequest request) throws Exception {
            return false;
        }

        public long createAndSpawn(AiaRobotSpawnRequest request) throws Exception {
            throw new UnsupportedOperationException("Connect ExampleServerRobotAdapter to your game server RobotFactory/World code.");
        }

        public void afterSpawn(AiaRobotSpawnRequest request, long serverObjectId) throws Exception {
        }
    }
}
