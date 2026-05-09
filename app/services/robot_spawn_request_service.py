from __future__ import annotations

import json
import time
from urllib.parse import urlparse

from app.core.config import settings
from app.models.request_models import RobotSpawnRequestCreateRequest
from app.services.robot_autonomy_baseline_service import robot_autonomy_baseline_service

try:
    import pymysql
except Exception:  # pragma: no cover
    pymysql = None


CLASS_IDS = {
    "royal": 0,
    "knight": 1,
    "elf": 2,
    "wizard": 3,
}


class RobotSpawnRequestService:
    def _connect(self):
        if pymysql is None:
            raise RuntimeError("pymysql_not_installed")
        parsed = urlparse(settings.db_bridge_mysql_dsn.replace("mysql+pymysql://", "mysql://"))
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

    def create_requests(self, request: RobotSpawnRequestCreateRequest) -> dict:
        if settings.db_bridge_backend.lower() != "mysql":
            return {
                "accepted": False,
                "reason": "db_bridge_backend_not_mysql",
                "required_table": "aia_robot_spawn_request",
                "created": 0,
                "submitted": 0,
                "affected": 0,
                "requests": [],
            }
        zones = self._enabled_zones() or [
            {
                "id": "fallback",
                "x": request.default_x,
                "y": request.default_y,
                "map_id": request.default_map,
                "min_level": request.level_min,
            }
        ]
        classes = [self._safe_class(item) for item in request.classes if self._safe_class(item)] or ["knight"]
        submitted_rows: list[dict] = []
        affected = 0
        try:
            with self._connect() as conn:
                for index in range(1, request.count + 1):
                    zone = zones[(index - 1) % len(zones)]
                    class_type = classes[(index - 1) % len(classes)]
                    row = self._build_row(request, index, zone, class_type)
                    affected += self._insert_row(conn, row)
                    submitted_rows.append(row)
            return {
                "accepted": True,
                "server_name": self._safe_token(request.server_name)[:64] or "main",
                "created": len(submitted_rows),
                "submitted": len(submitted_rows),
                "affected": affected,
                "duplicate_policy": "same request_id is updated; failed rows are reset to pending",
                "required_table": "aia_robot_spawn_request",
                "requests": [self._public_row(row) for row in submitted_rows],
            }
        except Exception as exc:
            return {
                "accepted": False,
                "reason": str(exc),
                "required_table": "aia_robot_spawn_request",
                "created": len(submitted_rows),
                "submitted": len(submitted_rows),
                "affected": affected,
                "requests": [self._public_row(row) for row in submitted_rows],
            }

    def _enabled_zones(self) -> list[dict]:
        config = robot_autonomy_baseline_service.load()
        zones = config.get("hunt_zones", []) if isinstance(config.get("hunt_zones"), list) else []
        return [zone for zone in zones if isinstance(zone, dict) and zone.get("enabled", True)]

    def _class_profile(self, class_type: str) -> dict:
        config = robot_autonomy_baseline_service.load()
        profiles = config.get("class_profiles", {}) if isinstance(config.get("class_profiles"), dict) else {}
        return profiles.get(class_type) or profiles.get("default") or {"role": "custom", "style": "balanced"}

    def _build_row(
        self,
        request: RobotSpawnRequestCreateRequest,
        index: int,
        zone: dict,
        class_type: str,
    ) -> dict:
        profile = self._class_profile(class_type)
        class_id = CLASS_IDS.get(class_type, 1)
        agent_id = "%s_%04d" % (self._safe_token(request.agent_prefix), index)
        request_id = "%s-%s" % (self._safe_token(request.request_prefix), agent_id)
        name = "%s%04d" % (request.name_prefix[:30], index)
        level = max(request.level_min, min(request.level_max, int(zone.get("min_level", request.level_min) or request.level_min)))
        loc_x = int(zone.get("x", request.default_x) or request.default_x) + ((index % 5) - 2)
        loc_y = int(zone.get("y", request.default_y) or request.default_y) + (((index // 5) % 5) - 2)
        loc_map = int(zone.get("map_id", request.default_map) or request.default_map)
        metadata = dict(request.metadata or {})
        metadata.update(
            {
                "source": "aia_spawn_request_api",
                "created_by": "AIA",
                "created_at": int(time.time()),
                "hunt_zone_id": zone.get("id", ""),
            }
        )
        return {
            "request_id": request_id[:64],
            "server_name": self._safe_token(request.server_name)[:64] or "main",
            "agent_id": agent_id[:64],
            "name": name[:45],
            "class_type": class_type[:20],
            "class_id": class_id,
            "level": level,
            "loc_x": loc_x,
            "loc_y": loc_y,
            "loc_map": loc_map,
            "heading": 0,
            "role": str(profile.get("role", "custom"))[:32],
            "style": str(profile.get("style", "balanced"))[:32],
            "home_x": loc_x,
            "home_y": loc_y,
            "home_map": loc_map,
            "hunt_zone_id": str(zone.get("id", ""))[:80],
            "priority": request.priority,
            "metadata_json": json.dumps(metadata, ensure_ascii=False),
        }

    def _insert_row(self, conn, row: dict) -> int:
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
                    row["request_id"],
                    row["server_name"],
                    row["agent_id"],
                    row["name"],
                    row["class_type"],
                    row["class_id"],
                    row["level"],
                    row["loc_x"],
                    row["loc_y"],
                    row["loc_map"],
                    row["heading"],
                    row["role"],
                    row["style"],
                    row["home_x"],
                    row["home_y"],
                    row["home_map"],
                    row["hunt_zone_id"],
                    row["priority"],
                    row["metadata_json"],
                ),
            )
            return int(cur.rowcount or 0)

    def _public_row(self, row: dict) -> dict:
        return {
            "request_id": row["request_id"],
            "agent_id": row["agent_id"],
            "name": row["name"],
            "class_type": row["class_type"],
            "level": row["level"],
            "loc_x": row["loc_x"],
            "loc_y": row["loc_y"],
            "loc_map": row["loc_map"],
            "status": "pending",
        }

    def _safe_class(self, value: str) -> str:
        return self._safe_token(str(value).strip().lower())[:20]

    def _safe_token(self, value: str) -> str:
        return "".join(ch for ch in str(value or "") if ch.isalnum() or ch in {"_", "-"})


robot_spawn_request_service = RobotSpawnRequestService()
