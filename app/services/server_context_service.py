from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


class ServerContextService:
    """Discover the host game server without assuming a specific server version."""

    def __init__(self) -> None:
        self.app_root = Path(__file__).resolve().parents[1]
        self.aia_root = self.app_root.parent
        self.profile_dir = self.app_root / "config" / "world_profiles"
        self._guide_cache: dict[str, Any] | None = None
        self._guide_cache_time = 0.0
        self._guide_cache_ttl = 60.0
        self._hunt_zone_cache: list[dict[str, Any]] | None = None
        self._hunt_zone_cache_time = 0.0

    def snapshot(self) -> dict[str, Any]:
        server_root = self._discover_server_root()
        mysql_conf = server_root / "mysql.conf" if server_root else None
        mysql = self._parse_mysql_conf(mysql_conf)
        database = mysql.get("database") or ""
        server_id = self._server_id(server_root, database)
        profile_path = self.ensure_world_profile(server_id, server_root, mysql)
        return {
            "server_id": server_id,
            "server_root": str(server_root) if server_root else "",
            "aia_root": str(self.aia_root),
            "mysql_conf": str(mysql_conf) if mysql_conf and mysql_conf.exists() else "",
            "mysql": mysql,
            "world_profile_path": str(profile_path),
            "robot_db_contract": ["robot", "robot_clan", "robot_setting"],
            "aia_db_contract": [
                "aia_robot_state",
                "aia_robot_event",
                "aia_robot_feedback",
                "aia_robot_decision",
                "aia_robot_trace_summary",
                "aia_robot_issue",
                "aia_robot_learning",
                "aia_robot_stall",
                "aia_robot_autofix",
                "aia_robot_metric",
                "aia_world_hunt_guide",
                "aia_world_siege_guide",
            ],
            "portable_contract": {
                "requires_robot_tables": False,
                "works_without_existing_robots": True,
                "server_version_agnostic": True,
                "server_reads": ["mysql.conf", "lineage.conf", "maps", "src"],
                "operator_tables": ["robot", "robot_clan", "robot_setting"],
            },
            "detected_assets": self._detected_assets(server_root),
            "world_guides": self.world_guides_snapshot(server_root, mysql),
        }

    def world_guides_snapshot(
        self,
        server_root: Path | None = None,
        mysql: dict[str, str] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        now = time.time()
        if not force and self._guide_cache is not None and now - self._guide_cache_time <= self._guide_cache_ttl:
            return self._guide_cache

        if server_root is None:
            server_root = self._discover_server_root()
        mysql_conf = server_root / "mysql.conf" if server_root else None
        mysql_values = self._parse_mysql_conf_private(mysql_conf)
        if mysql is None:
            mysql = self._parse_mysql_conf(mysql_conf)

        result: dict[str, Any] = {
            "enabled": False,
            "source": "aia_world_hunt_guide",
            "hunt_zone_count": 0,
            "siege_guide_count": 0,
            "sample_hunt_zones": [],
            "error": "",
        }
        database = mysql.get("database", "")
        mysql_bin = self._mysql_binary()
        if not database or not mysql_bin:
            result["error"] = "mysql_cli_or_database_not_available"
            self._guide_cache = result
            self._guide_cache_time = now
            return result

        try:
            hunt_rows = self._run_mysql_query(
                mysql_bin,
                mysql,
                mysql_values,
                "SELECT guide_id,map_id,anchor_x,anchor_y,min_level,max_level,recommended_level,guide_type,boss,weight "
                "FROM aia_world_hunt_guide ORDER BY min_level,map_id,weight DESC LIMIT 12",
            )
            count_rows = self._run_mysql_query(
                mysql_bin,
                mysql,
                mysql_values,
                "SELECT COUNT(*) FROM aia_world_hunt_guide",
            )
            siege_rows = self._run_mysql_query(
                mysql_bin,
                mysql,
                mysql_values,
                "SELECT COUNT(*) FROM aia_world_siege_guide",
            )
            result["enabled"] = True
            result["hunt_zone_count"] = self._to_int(count_rows[0][0] if count_rows else 0, 0)
            result["siege_guide_count"] = self._to_int(siege_rows[0][0] if siege_rows else 0, 0)
            result["sample_hunt_zones"] = [self._hunt_row_to_zone(row) for row in hunt_rows]
        except Exception as exc:
            result["error"] = str(exc)

        self._guide_cache = result
        self._guide_cache_time = now
        return result

    def world_hunt_zones(self, limit: int = 640) -> list[dict[str, Any]]:
        now = time.time()
        if self._hunt_zone_cache is not None and now - self._hunt_zone_cache_time <= self._guide_cache_ttl:
            return list(self._hunt_zone_cache)

        server_root = self._discover_server_root()
        mysql_conf = server_root / "mysql.conf" if server_root else None
        mysql = self._parse_mysql_conf(mysql_conf)
        mysql_values = self._parse_mysql_conf_private(mysql_conf)
        mysql_bin = self._mysql_binary()
        if not mysql.get("database") or not mysql_bin:
            return []
        try:
            rows = self._run_mysql_query(
                mysql_bin,
                mysql,
                mysql_values,
                "SELECT guide_id,map_id,anchor_x,anchor_y,min_level,max_level,recommended_level,guide_type,boss,weight "
                "FROM aia_world_hunt_guide ORDER BY min_level,map_id,weight DESC LIMIT "
                + str(max(1, min(2000, limit))),
            )
        except Exception:
            return []
        zones = [self._hunt_row_to_zone(row) for row in rows]
        self._hunt_zone_cache = zones
        self._hunt_zone_cache_time = now
        return list(zones)

    def ensure_world_profile(self, server_id: str, server_root: Path | None, mysql: dict[str, str]) -> Path:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        profile_path = self.profile_dir / f"{server_id}.json"
        payload = {
            "world_id": server_id,
            "display_name": server_id,
            "source": "aia_server_context",
            "server_root": str(server_root) if server_root else "",
            "mysql_database": mysql.get("database", ""),
            "mysql_host": mysql.get("host", ""),
            "robot_db_contract": ["robot", "robot_clan", "robot_setting"],
            "aia_policy_owner": "aia",
            "notes": [
                "AIA는 서버별 mysql.conf와 자산 구조를 읽어 이 서버 전용 프로필로 진화합니다.",
                "로봇북/토크/성장규칙 DB가 없어도 AIA 기본 정책과 학습 상태로 동작합니다.",
            ],
        }
        if profile_path.exists():
            try:
                current = json.loads(profile_path.read_text(encoding="utf-8"))
                if isinstance(current, dict):
                    current.update(payload)
                    payload = current
            except Exception:
                pass
        profile_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return profile_path

    def _discover_server_root(self) -> Path | None:
        env_root = os.getenv("AIA_SERVER_ROOT", "").strip()
        if env_root:
            path = Path(env_root)
            if path.exists():
                return path.resolve()
        for candidate in [self.aia_root.parent, *self.aia_root.parents]:
            if (candidate / "mysql.conf").exists() or (candidate / "lineage.conf").exists():
                return candidate.resolve()
        return self.aia_root.parent.resolve() if self.aia_root.parent.exists() else None

    def _parse_mysql_conf(self, path: Path | None) -> dict[str, str]:
        result = {"driver": "", "url": "", "host": "", "database": "", "user": "", "password_set": "false"}
        values = self._parse_mysql_conf_private(path)
        url = values.get("url", "")
        result["driver"] = values.get("driver", "")
        result["url"] = url
        result["user"] = values.get("id", values.get("user", ""))
        result["password_set"] = "true" if values.get("pw", values.get("password", "")) else "false"
        match = re.search(r"jdbc:mysql://([^/]+)/([^?]+)", url)
        if match:
            result["host"] = match.group(1)
            result["database"] = match.group(2)
        return result

    def _parse_mysql_conf_private(self, path: Path | None) -> dict[str, str]:
        result: dict[str, str] = {}
        if path is None or not path.exists():
            return result
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            result[key.strip().lower()] = value.strip()
        return result

    def _mysql_binary(self) -> str:
        configured = os.getenv("AIA_MYSQL_BIN", "").strip()
        if configured and Path(configured).exists():
            return configured
        found = shutil.which("mysql")
        if found:
            return found
        windows_default = Path("C:/Program Files/MySQL/MySQL Server 5.5/bin/mysql.exe")
        return str(windows_default) if windows_default.exists() else ""

    def _run_mysql_query(
        self,
        mysql_bin: str,
        mysql: dict[str, str],
        mysql_values: dict[str, str],
        query: str,
    ) -> list[list[str]]:
        command = [mysql_bin, "--default-character-set=utf8", "--batch", "--raw", "--skip-column-names"]
        host = mysql.get("host", "")
        if host:
            command.append("-h" + host.split(":", 1)[0])
        user = mysql.get("user", "")
        if user:
            command.append("-u" + user)
        password = mysql_values.get("pw", mysql_values.get("password", ""))
        if password:
            command.append("-p" + password)
        command.extend([mysql.get("database", ""), "-e", query])
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=4,
            check=True,
        )
        rows: list[list[str]] = []
        for line in completed.stdout.splitlines():
            if not line.strip():
                continue
            rows.append(line.split("\t"))
        return rows

    def _hunt_row_to_zone(self, row: list[str]) -> dict[str, Any]:
        guide_id = row[0] if len(row) > 0 else "unknown"
        map_id = self._to_int(row[1] if len(row) > 1 else 0, 0)
        guide_type = row[7] if len(row) > 7 else "normal"
        return {
            "id": "db_" + re.sub(r"[^A-Za-z0-9_.-]+", "_", guide_id),
            "name": f"DB map {map_id} lv {row[4] if len(row) > 4 else 1}-{row[5] if len(row) > 5 else 99}",
            "type": guide_type or "normal",
            "map_id": map_id,
            "x": self._to_int(row[2] if len(row) > 2 else 0, 0),
            "y": self._to_int(row[3] if len(row) > 3 else 0, 0),
            "min_level": self._to_int(row[4] if len(row) > 4 else 1, 1),
            "max_level": self._to_int(row[5] if len(row) > 5 else 999, 999),
            "recommended_level": self._to_int(row[6] if len(row) > 6 else 1, 1),
            "radius": 30 if guide_type in {"dungeon", "boss", "던전", "보스"} else 42,
            "teleport": guide_type not in {"beginner"},
            "enabled": True,
            "source": "aia_world_hunt_guide",
        }

    def _to_int(self, value: Any, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return default

    def _server_id(self, server_root: Path | None, database: str) -> str:
        raw = database or (server_root.name if server_root else "default")
        normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("._-")
        return normalized or "default"

    def _detected_assets(self, server_root: Path | None) -> dict[str, Any]:
        if server_root is None:
            return {}
        return {
            "has_java_src": (server_root / "src").exists(),
            "has_maps": (server_root / "maps").exists(),
            "has_client": (server_root / "SP163Client").exists(),
            "has_server_jar": (server_root / "server.jar").exists(),
            "map_count_hint": self._count_files(server_root / "maps", "*.txt"),
            "java_file_count_hint": self._count_files(server_root / "src", "*.java"),
        }

    def _count_files(self, path: Path, pattern: str) -> int:
        if not path.exists():
            return 0
        try:
            return sum(1 for _ in path.rglob(pattern))
        except Exception:
            return 0


server_context_service = ServerContextService()
