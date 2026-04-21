import json
from datetime import datetime
from pathlib import Path

from app.core.config import settings


class LearningJournalService:
    def __init__(self) -> None:
        self.enabled = settings.learning_journal_enabled
        self.base_path = Path(settings.learning_journal_path)
        self.keep_last = max(1, settings.learning_journal_keep_last)
        if self.enabled:
            self.base_path.mkdir(parents=True, exist_ok=True)

    def append(self, agent_id: str, payload: dict) -> dict:
        if not self.enabled:
            return {"stored": False, "reason": "disabled"}
        agent_dir = self.base_path / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        target = agent_dir / f"{stamp}.json"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._trim(agent_dir)
        return {"stored": True, "path": str(target)}

    def clear(self, agent_id: str) -> dict:
        if not self.enabled:
            return {"cleared": False, "reason": "disabled"}
        agent_dir = self.base_path / agent_id
        if not agent_dir.exists():
            return {"cleared": True, "removed": 0}
        removed = 0
        for file in agent_dir.glob("*.json"):
            file.unlink(missing_ok=True)
            removed += 1
        return {"cleared": True, "removed": removed}

    def _trim(self, agent_dir: Path) -> None:
        files = sorted(agent_dir.glob("*.json"))
        if len(files) <= self.keep_last:
            return
        for file in files[:-self.keep_last]:
            file.unlink(missing_ok=True)


learning_journal_service = LearningJournalService()
