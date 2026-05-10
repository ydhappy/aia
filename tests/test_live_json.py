from pathlib import Path

from app.core.live_json import LiveJsonFile


def test_live_json_reload_on_file_change(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    loader = LiveJsonFile(path, fallback=lambda: {"version": 0})

    assert loader.load() == {"version": 0}

    path.write_text('{"version": 1, "name": "first"}\n', encoding="utf-8")
    assert loader.load() == {"version": 1, "name": "first"}

    path.write_text('{"version": 2, "name": "second"}\n', encoding="utf-8")
    assert loader.load() == {"version": 2, "name": "second"}


def test_live_json_save_updates_cache(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    loader = LiveJsonFile(path, fallback=lambda: {})
    saved = loader.save({"enabled": True})
    assert saved == {"enabled": True}
    assert loader.load() == {"enabled": True}
    assert loader.info()["live_reload"] is True
