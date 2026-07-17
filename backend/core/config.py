import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# หา path ของ .env แบบ absolute โดยอิงจากตำแหน่งไฟล์นี้เอง
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)  # ชี้ไปที่ backend/
ENV_PATH = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):
    APP_NAME: str = "Backend Service"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5432/dbname"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    LABEL_STUDIO_URL: str = "http://localhost:8080"
    LABEL_STUDIO_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
