import json
from pathlib import Path


class WorldProfileService:
    def __init__(self) -> None:
        self.base_path = Path(__file__).resolve().parents[1] / "config" / "world_profiles"

    def load(self, world_id: str | None = None) -> dict:
        world_id = world_id or "default"
        target = self.base_path / f"{world_id}.json"
        default_file = self.base_path / "default.json"

        if target.exists():
            return json.loads(target.read_text(encoding="utf-8"))
        if default_file.exists():
            return json.loads(default_file.read_text(encoding="utf-8"))
        return {"world_id": world_id, "defaults": {}, "maps": {}}


world_profile_service = WorldProfileService()
