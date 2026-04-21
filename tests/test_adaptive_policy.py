from app.models.response_models import DecideResponse
from app.services.adaptive_policy import adaptive_policy


def test_preferred_action_bias_increases_confidence() -> None:
    decision = DecideResponse(
        action="ATTACK",
        action_args={},
        confidence=0.5,
        reason="base",
        source="rule_engine",
    )
    adjusted = adaptive_policy.adjust(decision, {"preferred_action": "ATTACK"})
    assert adjusted.confidence > 0.5


def test_avoid_action_penalty_decreases_confidence() -> None:
    decision = DecideResponse(
        action="RETREAT",
        action_args={},
        confidence=0.8,
        reason="base",
        source="rule_engine",
    )
    adjusted = adaptive_policy.adjust(decision, {"avoid_action": "RETREAT"})
    assert adjusted.confidence < 0.8
