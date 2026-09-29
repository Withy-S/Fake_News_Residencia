from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FN_")

    min_text_length: int = 20
    min_confidence: float = 0.6
    classifier: str = "placeholder"
    ensemble_members: list[str] = []
    ensemble_weights: dict[str, float] = {}
    bertimbau_model_path: str = "../ml/modelos/bertimbau-fakebr"
    bertimbau_fake_label: str = "LABEL_1"
    fallback_method: str = "ai_fallback"
    trusted_domains: list[str] = []
    request_timeout_seconds: float = 10.0
    classifier_timeout_seconds: float = 5.0
    allowed_origins: list[str] = []


settings = Settings()
