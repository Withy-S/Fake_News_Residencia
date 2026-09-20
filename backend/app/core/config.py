from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FN_")

    min_text_length: int = 20
    min_confidence: float = 0.6
    fallback_method: str = "ai_fallback"
    trusted_domains: list[str] = []
    request_timeout_seconds: float = 10.0
    allowed_origins: list[str] = []


settings = Settings()
