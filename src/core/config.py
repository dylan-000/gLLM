from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", case_sensitive=True
    )

    DATABASE_URL: str
    BUCKET_NAME: str
    APP_AWS_ACCESS_KEY: str
    APP_AWS_SECRET_KEY: str
    APP_AWS_REGION: str
    AUTH_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    HASH_ALGORITHM: str
