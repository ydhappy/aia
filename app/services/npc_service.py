from app.services.economy_service import economy_service
from app.services.store_factory import store


class NPCService:
    def next_npc_step(self, agent_id: str) -> dict:
        eco = economy_service.next_economy_step(agent_id)
        profile = store.get_profile(agent_id) or {}
        home_x = profile.get("home_x")
        home_y = profile.get("home_y")

        if eco.get("phase") == "inventory_reset":
            return {
                "phase": "npc_interaction",
                "objective": "sell_store_inventory",
                "npc_type": "merchant",
                "home_x": home_x,
                "home_y": home_y,
            }
        if eco.get("phase") == "resupply":
            return {
                "phase": "npc_interaction",
                "objective": "buy_consumables",
                "npc_type": "shopkeeper",
                "home_x": home_x,
                "home_y": home_y,
            }
        return {
            "phase": "none",
            "objective": "no_npc_interaction_needed",
        }


npc_service = NPCService()
