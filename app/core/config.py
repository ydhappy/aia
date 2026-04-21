from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AIA"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_env: str = "dev"
    log_level: str = "INFO"

    llm_backend: str = "none"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:3b-instruct"
    llm_timeout_seconds: float = 3.0
    llm_api_key: str = ""
    llm_provider: str = "generic"

    state_store_mode: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    db_bridge_backend: str = "sqlite"
    db_bridge_sqlite_path: str = "./aia_bridge.db"
    db_bridge_postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/aia"
    db_bridge_mysql_dsn: str = "mysql+pymysql://root:root@localhost:3306/aia"
    default_retreat_hp_threshold: int = 30
    default_heal_hp_threshold: int = 50

    adaptive_preferred_bonus: float = 0.05
    adaptive_avoid_penalty: float = 0.15
    learning_reward_decay: float = 0.98

    enable_api_key_auth: bool = False
    api_key: str = ""
    allow_batch_requests: bool = True
    max_batch_size: int = 50

    enable_websocket_gateway: bool = True


settings = Settings()
