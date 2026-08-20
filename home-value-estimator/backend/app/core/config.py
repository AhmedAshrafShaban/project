import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    model_path: str = os.getenv("MODEL_PATH", "models/home_value_pipeline.pkl")
    metrics_path: str = os.getenv("METRICS_PATH", "models/model_metrics.json")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cors_origins: list = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
        ).split(",")
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
