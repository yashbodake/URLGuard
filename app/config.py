"""Application configuration using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Pydantic settings for the URLGuard app."""

    model_path: Path = Path("data/model/rf_model.joblib")
    risk_threshold: float = 0.4
    max_batch_size: int = 100
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
