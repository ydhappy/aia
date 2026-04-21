from app.services.llm_parser import llm_parser


def test_parse_valid_json_response() -> None:
    raw = '{"action":"ATTACK","action_args":{"target_id":"mob_1"},"confidence":0.9,"reason":"target_in_range"}'
    result = llm_parser.parse_decision(raw)
    assert result is not None
    assert result.action == "ATTACK"


def test_parse_json_wrapped_in_text() -> None:
    raw = 'result: {"action":"IDLE","action_args":{},"confidence":0.4,"reason":"uncertain"}'
    result = llm_parser.parse_decision(raw)
    assert result is not None
    assert result.action == "IDLE"


def test_parse_invalid_response_returns_none() -> None:
    raw = 'not a json response'
    result = llm_parser.parse_decision(raw)
    assert result is None
