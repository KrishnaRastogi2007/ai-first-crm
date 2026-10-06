"""
Environment variables/configuration.

Example:

DATABASE_URL
GROQ_API_KEY
SECRET_KEY

"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    DATABASE_URL: str
    JWT_SECRET_KEY: str

    INITIAL_ADMIN_NAME:str
    INITIAL_ADMIN_EMAIL:str
    INITIAL_ADMIN_PASSWORD:str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
