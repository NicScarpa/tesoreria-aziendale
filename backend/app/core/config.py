from pathlib import Path

from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _root = Path(__file__).resolve().parents[3]
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=(
            str(_root / ".env"),
            str(_root / "backend" / ".env"),
        ),
        env_file_encoding="utf-8",
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    FERNET_KEY: str = ""
    ADE_LOGIN_URL: str = ""


settings = Settings()

# Auto-generate FERNET_KEY if not configured (dev convenience)
if not settings.FERNET_KEY:
    settings.FERNET_KEY = Fernet.generate_key().decode()
