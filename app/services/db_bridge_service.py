class DBBridgeService:
    def poll_states(self) -> list[dict]:
        return []

    def poll_events(self) -> list[dict]:
        return []

    def poll_feedback(self) -> list[dict]:
        return []

    def write_decision(self, decision_row: dict) -> dict:
        return {"written": True, "row": decision_row}

    def write_trace_summary(self, trace_row: dict) -> dict:
        return {"written": True, "row": trace_row}


db_bridge_service = DBBridgeService()
