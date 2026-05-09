import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import pymysql

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.robot_autonomy_baseline_service import robot_autonomy_baseline_service


CLASS_IDS = {
    "royal": 0,
    "knight": 1,
    "elf": 2,
    "wizard": 3,
}


def connect(mysql_dsn: str):
    parsed = urlparse(mysql_dsn.replace("mysql+pymysql://", "mysql://"))
    return pymysql.connect(
        host=parsed.hostname or "localhost",
        port=parsed.port or 3306,
        user=parsed.username or "root",
        password=parsed.password or "",
        database=(parsed.path or "/aia").lstrip("/"),
        autocommit=True,
        charset="utf8",
        cursorclass=pymysql.cursors.DictCursor,
    )


def enabled_zones() -> list[dict]:
    config = robot_autonomy_baseline_service.load()
    zones = config.get("hunt_zones", []) if isinstance(config.get("hunt_zones"), list) else []
    return [zone for zone in zones if isinstance(zone, dict) and zone.get("enabled", True)]


def class_profile(class_type: str) -> dict:
    config = robot_autonomy_baseline_service.load()
    profiles = config.get("class_profiles", {}) if isinstance(config.get("class_profiles"), dict) else {}
    return profiles.get(class_type) or profiles.get("default") or {"role": "custom", "style": "balanced"}


def insert_request(conn, args, index: int, zone: dict, class_type: str) -> None:
    profile = class_profile(class_type)
    class_id = CLASS_IDS.get(class_type, 1)
    agent_id = "%s_%04d" % (args.agent_prefix, index)
    request_id = "%s-%s" % (args.request_prefix, agent_id)
    name = "%s%04d" % (args.name_prefix, index)
    level = max(args.level_min, min(args.level_max, int(zone.get("min_level", args.level_min) or args.level_min)))
    loc_x = int(zone.get("x", args.default_x) or args.default_x)
    loc_y = int(zone.get("y", args.default_y) or args.default_y)
    loc_map = int(zone.get("map_id", args.default_map) or args.default_map)
    radius = int(zone.get("radius", 20) or 20)
    loc_x += (index % 5) - 2
    loc_y += ((index // 5) % 5) - 2
    metadata = {
        "source": "aia_seed_robot_spawn_requests_mysql55",
        "zone_radius": radius,
        "created_by": "AIA",
        "created_at": int(time.time()),
    }
    sql = """
        INSERT INTO aia_robot_spawn_request
        (request_id, server_name, agent_id, name, class_type, class_id, level,
         loc_x, loc_y, loc_map, heading, role, style, home_x, home_y, home_map,
         hunt_zone_id, priority, metadata_json)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = IF(status = 'failed', 'pending', status),
            priority = VALUES(priority),
            metadata_json = VALUES(metadata_json)
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                request_id,
                args.server_name,
                agent_id,
                name,
                class_type,
                class_id,
                level,
                loc_x,
                loc_y,
                loc_map,
                0,
                profile.get("role", "custom"),
                profile.get("style", "balanced"),
                loc_x,
                loc_y,
                loc_map,
                zone.get("id", ""),
                args.priority,
                json.dumps(metadata, ensure_ascii=False),
            ),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed AIA robot spawn requests for MySQL 5.5 game servers.")
    parser.add_argument("--mysql-dsn", required=True, help="mysql+pymysql://user:pass@host:3306/db")
    parser.add_argument("--server-name", default="main")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--request-prefix", default="aia-boot")
    parser.add_argument("--agent-prefix", default="aia_robot")
    parser.add_argument("--name-prefix", default="AIA로봇")
    parser.add_argument("--classes", default="knight,elf,wizard")
    parser.add_argument("--level-min", type=int, default=1)
    parser.add_argument("--level-max", type=int, default=30)
    parser.add_argument("--priority", type=int, default=100)
    parser.add_argument("--default-x", type=int, default=32670)
    parser.add_argument("--default-y", type=int, default=32790)
    parser.add_argument("--default-map", type=int, default=4)
    args = parser.parse_args()

    zones = enabled_zones() or [{"id": "fallback", "x": args.default_x, "y": args.default_y, "map_id": args.default_map, "min_level": args.level_min}]
    classes = [item.strip() for item in args.classes.split(",") if item.strip()] or ["knight"]
    with connect(args.mysql_dsn) as conn:
        for index in range(1, args.count + 1):
            zone = zones[(index - 1) % len(zones)]
            class_type = classes[(index - 1) % len(classes)]
            insert_request(conn, args, index, zone, class_type)
    print("AIA_ROBOT_SPAWN_REQUESTS_SEEDED=%d" % args.count)


if __name__ == "__main__":
    main()
