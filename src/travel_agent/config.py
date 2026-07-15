"""Application configuration via environment variables.

Uses pydantic-settings to load from .env file automatically.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings loaded from environment / .env file."""

    # ── LLM Provider ──
    LLM_PROVIDER: str = "openai"
    """Provider: openai | deepseek | glm"""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"

    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"

    # GLM (Zhipu AI)
    GLM_API_KEY: str = ""
    GLM_MODEL_NAME: str = "glm-4"

    # LBS (future)
    AMAP_API_KEY: str = ""

    # Weather (future)
    WEATHER_API_KEY: str = ""

    # App
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
