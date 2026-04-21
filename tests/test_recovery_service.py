from app.services.recovery_service import recovery_service
from app.services.store_factory import store


def test_recovery_low_hp_triggers_retreat() -> None:
    store.save_state("bot_recover_1", 1, {"hp": 10, "mp": 5})
    result = recovery_service.recover_agent("bot_recover_1")
    assert result.action == "force_retreat"


def test_recovery_without_state_returns_noop() -> None:
    result = recovery_service.recover_agent("bot_recover_missing")
    assert result.action == "noop"
