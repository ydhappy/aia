package integration.java8;

/**
 * 게임서버 내부 캐릭터/로봇 객체를 AIA 요청 JSON으로 바꾸는 클래스입니다.
 *
 * 초보자용 핵심:
 * 1) 처음에는 필요한 값만 넣으세요.
 * 2) hp/mp/x/y/map 정도부터 시작해도 됩니다.
 * 3) 아래 TODO 주석 부분만 현재 서버 구조에 맞게 수정하면 됩니다.
 */
public class RobotStateExtractor {

    /**
     * 서버 캐릭터 객체 대신 초보자가 바로 이해할 수 있도록
     * 최소 상태 전송용 단순 모델을 같이 제공합니다.
     */
    public static class RobotSnapshot {
        public String agentId;
        public long tick;
        public int hp;
        public int maxHp;
        public int hpPercent;
        public int mp;
        public int x;
        public int y;
        public int mapId;
        public String targetId;
        public int targetDistance;
        public boolean safeZone;
        public int weightPercent;
        public int potionCount;
        public boolean underAttack;
        public boolean canTeleport;
        public int level;
        public int robotUid;
        public int localAreaLevel;
        public int nearbyMonsterMaxLevel;
        public boolean dangerHotspot;
        public boolean teleportHuntEnabled;
    }

    public String toDecideJson(RobotSnapshot s) {
        return "{"
                + "\"agent_id\":\"" + esc(s.agentId) + "\","
                + "\"tick\":" + s.tick + ","
                + "\"state\":{"
                + "\"hp\":" + s.hp + ","
                + "\"mp\":" + s.mp + ","
                + "\"x\":" + s.x + ","
                + "\"y\":" + s.y + ","
                + "\"map_id\":" + s.mapId + ","
                + "\"target_id\":" + nullableString(s.targetId) + ","
                + "\"target_distance\":" + s.targetDistance + ","
                + "\"safe_zone\":" + s.safeZone + ","
                + "\"weight_percent\":" + s.weightPercent + ","
                + "\"inventory\":{\"potion\":" + s.potionCount + "},"
                + "\"is_under_attack\":" + s.underAttack + ","
                + "\"can_teleport\":" + s.canTeleport + ","
                + "\"extras\":{"
                + "\"level\":" + s.level + ","
                + "\"robot_level\":" + s.level + ","
                + "\"robot_uid\":" + s.robotUid + ","
                + "\"actor_kind\":\"robot\","
                + "\"local_area_level\":" + s.localAreaLevel + ","
                + "\"nearby_monster_max_level\":" + s.nearbyMonsterMaxLevel + ","
                + "\"danger_hotspot\":" + s.dangerHotspot + ","
                + "\"teleport_hunt_enabled\":" + s.teleportHuntEnabled
                + "}"
                + "}"
                + "}";
    }

    /**
     * TODO: 아래 메서드는 실제 서버 플레이어/캐릭터 객체 타입에 맞게 수정하세요.
     *
     * 사용 예시:
     * - L1PcInstance pc
     * - Player pc
     * - CharacterInstance pc
     *
     * 해야 할 일:
     * - 아래 더미 값을 현재 서버의 getter로 바꾸기
     */
    public RobotSnapshot fromServerObject(Object serverRobotObject) {
        RobotSnapshot s = new RobotSnapshot();

        // TODO 1: 아래 agentId는 현재 서버의 캐릭터명/오브젝트ID/계정명 중 하나로 바꾸세요.
        s.agentId = "bot_001";

        // TODO 2: 현재 서버 tick 또는 System.currentTimeMillis() 기반 값으로 바꾸세요.
        s.tick = System.currentTimeMillis();

        // TODO 3: 아래 값들을 실제 서버 객체 getter로 바꾸세요.
        s.hp = 100;
        s.maxHp = 100;
        s.hpPercent = 100;
        s.mp = 50;
        s.x = 0;
        s.y = 0;
        s.mapId = 0;
        s.targetId = null;
        s.targetDistance = 0;
        s.safeZone = false;
        s.weightPercent = 0;
        s.potionCount = 0;
        s.underAttack = false;
        s.canTeleport = true;
        s.level = 1;
        s.robotUid = 0;
        s.localAreaLevel = 0;
        s.nearbyMonsterMaxLevel = 0;
        s.dangerHotspot = false;
        s.teleportHuntEnabled = true;

        return s;
    }

    private String esc(String value) {
        if (value == null) return "";
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private String nullableString(String value) {
        if (value == null) {
            return "null";
        }
        return "\"" + esc(value) + "\"";
    }
}
