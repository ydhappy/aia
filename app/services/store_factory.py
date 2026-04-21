from app.core.config import settings
from app.services.redis_store import RedisStore
from app.services.state_store import state_store as memory_store


def get_state_store():
    if settings.state_store_mode.lower() == "redis":
        return RedisStore()
    return memory_store


store = get_state_store()
