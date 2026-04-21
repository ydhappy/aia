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

    state_store_mode: str = "memory"
    default_retreat_hp_threshold: int = 30
    default_heal_hp_threshold: int = 50


settings = Settings()
