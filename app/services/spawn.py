from __future__ import annotations

import json
import time

from app.core.config import settings
from app.core.mysql import connect_mysql
from app.core.names import ClassId, SpawnStatus, Table
from app.models.request_models import RobotSpawnRequestCreateRequest
from app.services.autonomy import robot_autonomy_baseline_service


class RobotSpawnRequestService:
    def _connect(self):
        return connect_mysql(settings.db_bridge_mysql_dsn)

    def create_requests(self, request: RobotSpawnRequestCreateRequest) -> dict:
        if settings.db_bridge_backend.lower() != "mysql":
            return self._result(False, "db_bridge_backend_not_mysql")
        rows: list[dict] = []
        affected = 0
        zones = self._zones(request)
        classes = [self._safe_class(v) for v in request.classes if self._safe_class(v)] or ["knight"]
        try:
            with self._connect() as conn:
                for index in range(1, request.count + 1):
                    row = self._row(request, index, zones[(index - 1) % len(zones)], classes[(index - 1) % len(classes)])
                    affected += self._insert(conn, row)
                    rows.append(row)
            return self._result(True, "", rows, affected, request.server_name)
        except Exception as exc:
            return self._result(False, str(exc), rows, affected, request.server_name)

    def _result(self, accepted: bool, reason: str = "", rows: list[dict] | None = None, affected: int = 0, server_name: str = "main") -> dict:
        rows = rows or []
        data = {
            "accepted": accepted,
            "required_table": Table.SPAWN,
            "created": len(rows),
            "submitted": len(rows),
            "affected": affected,
            "requests": [self._public(row) for row in rows],
        }
        if accepted:
            data.update({"server_name": self._safe_token(server_name)[:64] or "main", "duplicate_policy": "same request_id is updated; failed rows are reset to pending"})
        else:
            data["reason"] = reason
        return data

    def _zones(self, request: RobotSpawnRequestCreateRequest) -> list[dict]:
        config = robot_autonomy_baseline_service.load()
        zones = config.get("hunt_zones", []) if isinstance(config.get("hunt_zones"), list) else []
        enabled = [zone for zone in zones if isinstance(zone, dict) and zone.get("enabled", True)]
        return enabled or [{"id": "fallback", "x": request.default_x, "y": request.default_y, "map_id": request.default_map, "min_level": request.level_min}]

    def _profile(self, class_type: str) -> dict:
        config = robot_autonomy_baseline_service.load()
        profiles = config.get("class_profiles", {}) if isinstance(config.get("class_profiles"), dict) else {}
        return profiles.get(class_type) or profiles.get("default") or {"role": "custom", "style": "balanced"}

    def _row(self, request: RobotSpawnRequestCreateRequest, index: int, zone: dict, class_type: str) -> dict:
        profile = self._profile(class_type)
        agent_id = "%s_%04d" % (self._safe_token(request.agent_prefix), index)
        level = max(request.level_min, min(request.level_max, int(zone.get("min_level", request.level_min) or request.level_min)))
        x = int(zone.get("x", request.default_x) or request.default_x) + ((index % 5) - 2)
        y = int(zone.get("y", request.default_y) or request.default_y) + (((index // 5) % 5) - 2)
        map_id = int(zone.get("map_id", request.default_map) or request.default_map)
        metadata = dict(request.metadata or {})
        metadata.update({"source": "aia_spawn_request_api", "created_by": "AIA", "created_at": int(time.time()), "hunt_zone_id": zone.get("id", "")})
        return {
            "request_id": ("%s-%s" % (self._safe_token(request.request_prefix), agent_id))[:64],
            "server_name": self._safe_token(request.server_name)[:64] or "main",
            "agent_id": agent_id[:64],
            "name": ("%s%04d" % (request.name_prefix[:30], index))[:45],
            "class_type": class_type[:20],
            "class_id": ClassId.BY_NAME.get(class_type, ClassId.KNIGHT),
            "level": level,
            "loc_x": x,
            "loc_y": y,
            "loc_map": map_id,
            "heading": 0,
            "role": str(profile.get("role", "custom"))[:32],
            "style": str(profile.get("style", "balanced"))[:32],
            "home_x": x,
            "home_y": y,
            "home_map": map_id,
            "hunt_zone_id": str(zone.get("id", ""))[:80],
            "priority": request.priority,
            "metadata_json": json.dumps(metadata, ensure_ascii=False),
        }

    def _insert(self, conn, row: dict) -> int:
        columns = ["request_id", "server_name", "agent_id", "name", "class_type", "class_id", "level", "loc_x", "loc_y", "loc_map", "heading", "role", "style", "home_x", "home_y", "home_map", "hunt_zone_id", "priority", "metadata_json"]
        sql = "INSERT INTO %s (%s) VALUES (%s) ON DUPLICATE KEY UPDATE status = IF(status = 'failed', 'pending', status), priority = VALUES(priority), metadata_json = VALUES(metadata_json)" % (Table.SPAWN, ", ".join(columns), ", ".join(["%s"] * len(columns)))
        with conn.cursor() as cur:
            cur.execute(sql, tuple(row[col] for col in columns))
            return int(cur.rowcount or 0)

    def _public(self, row: dict) -> dict:
        return {"request_id": row["request_id"], "agent_id": row["agent_id"], "name": row["name"], "class_type": row["class_type"], "level": row["level"], "loc_x": row["loc_x"], "loc_y": row["loc_y"], "loc_map": row["loc_map"], "status": SpawnStatus.PENDING}

    def _safe_class(self, value: str) -> str:
        return self._safe_token(str(value).strip().lower())[:20]

    def _safe_token(self, value: str) -> str:
        return "".join(ch for ch in str(value or "") if ch.isalnum() or ch in {"_", "-"})


robot_spawn_request_service = RobotSpawnRequestService()

__all__ = ["RobotSpawnRequestService", "robot_spawn_request_service"]
