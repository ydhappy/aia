from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


class LiveJsonFile:
    """Small JSON loader that reloads on file mtime change.

    Use this for operator-editable JSON files. The next request after a file edit
    sees the new content without restarting AIA.
    """

    def __init__(self, path: Path, fallback: Callable[[], dict[str, Any]] | None = None) -> None:
        self.path = path
        self.fallback = fallback or (lambda: {})
        self._cache: dict[str, Any] | None = None
        self._mtime: float = -1.0

    def load(self, force: bool = False) -> dict[str, Any]:
        if not self.path.exists():
            self._cache = self.fallback()
            self._mtime = -1.0
            return dict(self._cache)
        mtime = self.path.stat().st_mtime
        if not force and self._cache is not None and mtime == self._mtime:
            return dict(self._cache)
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            loaded = self.fallback()
        if not isinstance(loaded, dict):
            loaded = self.fallback()
        self._cache = loaded
        self._mtime = mtime
        return dict(loaded)

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        safe = data if isinstance(data, dict) else self.fallback()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return self.load(force=True)

    def info(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "exists": self.path.exists(),
            "mtime": self._mtime,
            "live_reload": True,
        }
