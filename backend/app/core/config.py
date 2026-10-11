# Centralized application configuration.

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/.env ka absolute path
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = Field(min_length=1)
    APP_ENV: Literal["development", "testing", "production"]

    DATABASE_URL: str = Field(min_length=1)

    JWT_SECRET_KEY: str = Field(min_length=32)
    JWT_REFRESH_SECRET_KEY: str = Field(min_length=32)

    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        gt=0,
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        gt=0,
    )

    INITIAL_ADMIN_NAME: str = Field(min_length=1)
    INITIAL_ADMIN_EMAIL: str = Field(min_length=3)
    INITIAL_ADMIN_PASSWORD: str = Field(min_length=12)

    @field_validator("APP_NAME", "INITIAL_ADMIN_NAME", "INITIAL_ADMIN_EMAIL")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        """Reject values containing only whitespace."""
        value = value.strip()
        if not value:
            raise ValueError("This setting cannot be empty.")
        return value

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()