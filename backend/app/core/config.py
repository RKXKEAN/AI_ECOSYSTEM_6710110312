import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find path of .env relative to this config file
# Since this file is in backend/app/core/config.py, BASE_DIR goes up 3 levels to reach backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):
    APP_NAME: str = "Backend Service"
    DEBUG: bool = False
    JWT_SECRET_KEY: str = "dev-secret-change-me"

    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5432/dbname"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    LABEL_STUDIO_URL: str = "http://localhost:8080"
    LABEL_STUDIO_API_KEY: str = ""

    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = Field(default="my-photos", validation_alias="MINIO_BUCKET")

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
