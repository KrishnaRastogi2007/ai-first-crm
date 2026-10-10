from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int =15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    INITIAL_ADMIN_NAME:str
    INITIAL_ADMIN_EMAIL:str
    INITIAL_ADMIN_PASSWORD:str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
