class RebalanceService:
    def recommend(self, shards: list[dict]) -> dict:
        if not shards:
            return {"recommended": False, "moves": []}
        sorted_shards = sorted(shards, key=lambda s: s.get("weight", 0))
        light = sorted_shards[0]
        heavy = sorted_shards[-1]
        if heavy.get("weight", 0) - light.get("weight", 0) < 2:
            return {"recommended": False, "moves": []}
        source_agents = heavy.get("agent_ids", [])
        if not source_agents:
            return {"recommended": False, "moves": []}
        return {
            "recommended": True,
            "moves": [
                {
                    "agent_id": source_agents[-1],
                    "from": heavy.get("shard_key"),
                    "to": light.get("shard_key"),
                }
            ],
        }


rebalance_service = RebalanceService()
