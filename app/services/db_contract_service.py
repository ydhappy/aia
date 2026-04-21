class DBContractService:
    def state_row_example(self) -> dict:
        return {
            "agent_id": "bot_001",
            "tick": 1001,
            "hp": 88,
            "mp": 20,
            "x": 100,
            "y": 200,
            "map_id": 4,
            "target_id": "mob_1",
            "target_distance": 1,
            "safe_zone": False,
            "weight_percent": 45,
        }

    def event_row_example(self) -> dict:
        return {
            "agent_id": "bot_001",
            "tick": 1002,
            "event_type": "loot_detected",
            "severity": "low",
            "message": "rare drop seen",
        }

    def feedback_row_example(self) -> dict:
        return {
            "agent_id": "bot_001",
            "tick": 1003,
            "action": "ATTACK",
            "reward": 1.0,
            "outcome": "success",
            "map_id": 4,
        }


db_contract_service = DBContractService()
