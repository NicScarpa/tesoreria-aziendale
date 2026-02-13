import logging
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)


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

if not settings.FERNET_KEY:
    _generated_key = Fernet.generate_key().decode()
    settings.FERNET_KEY = _generated_key
    _env_path = Path(__file__).resolve().parents[3] / ".env"
    try:
        with open(_env_path, "a") as f:
            f.write(f"\nFERNET_KEY={_generated_key}\n")
        _logger.warning("FERNET_KEY auto-generata e salvata in %s", _env_path)
    except OSError as e:
        _logger.error("Impossibile salvare FERNET_KEY in %s: %s", _env_path, e)
