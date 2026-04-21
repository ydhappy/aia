from app.services.store_factory import store


class EconomyService:
    def next_economy_step(self, agent_id: str) -> dict:
        state_wrapper = store.get_state(agent_id) or {}
        state = state_wrapper.get("state", {}) if isinstance(state_wrapper, dict) else {}
        inventory = state.get("inventory", {}) or {}
        weight_percent = int(state.get("weight_percent", 0) or 0)
        potion_count = int(inventory.get("potion", 0) or 0)
        safe_zone = bool(state.get("safe_zone", False))

        if weight_percent >= 85 and not safe_zone:
            return {"phase": "return_base", "objective": "return_for_inventory_reset"}
        if safe_zone and weight_percent >= 85:
            return {"phase": "inventory_reset", "objective": "store_or_sell_items"}
        if safe_zone and potion_count <= 2:
            return {"phase": "resupply", "objective": "buy_or_fetch_potions"}
        if safe_zone:
            return {"phase": "redeploy", "objective": "leave_safe_zone_and_resume"}
        return {"phase": "field_operation", "objective": "continue_field_loop"}


economy_service = EconomyService()
