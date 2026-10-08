from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FN_")

    min_text_length: int = 20
    min_confidence: float = 0.6
    classifier: str = "stacking"
    ensemble_members: list[str] = []
    ensemble_weights: dict[str, float] = {}
    stacking_model_path: str = "models/stacking.joblib"
    fallback_method: str = "ai_fallback"
    trusted_domains: list[str] = []
    request_timeout_seconds: float = 10.0
    classifier_timeout_seconds: float = 5.0
    allowed_origins: list[str] = []


settings = Settings()
