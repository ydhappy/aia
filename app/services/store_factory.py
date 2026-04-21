from app.core.config import settings
from app.services.state_store import state_store as memory_store


def get_state_store():
    # Redis store can be plugged in later when state_store_mode is switched.
    # Current default remains memory for safe startup.
    return memory_store


store = get_state_store()
