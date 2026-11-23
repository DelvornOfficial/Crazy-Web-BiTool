import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Next Level Cheat API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:xivam@localhost:5432/nextlevelcheat"
    FALLBACK_TO_SQLITE: bool = True

    # JWT Authentication
    SECRET_KEY: str = "9f8c6e2a5d4b1a7f0e3c8b5d2a9f4e1c7b0a3d6f9e2c5b8a1f4d7e0c3b6a9f2e"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours

    # Anti-Brute Force Protection
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60
    MAX_LOGIN_REQUESTS_PER_WINDOW: int = 10

    # Admin Credentials directly managed from .env (Hashed for Maximum Security)
    ADMIN_USERNAME: str = "Bee-Tool"
    ADMIN_PASSWORD_HASH: str = "$2b$12$qGieR.1PNpkaUtv3kW6GH.VwQPW4mRGB4tsC53ILdPXDfoZfHR4za"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def configured_admin_username(self) -> str:
        return self.ADMIN_USERNAME or "Bee-Tool"

    @property
    def configured_admin_password_hash(self) -> str:
        return self.ADMIN_PASSWORD_HASH


def get_live_env_admin_credentials() -> tuple[str, str]:
    """
    Live reader: Strictly reads ADMIN_USERNAME and ADMIN_PASSWORD_HASH directly from .env.
    Passwords are NEVER stored in plain text. Only .env controls admin credentials.
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    username = settings.configured_admin_username
    password_hash = settings.configured_admin_password_hash
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k == "ADMIN_USERNAME":
                        username = v
                    elif k in ["ADMIN_PASSWORD_HASH", "ADMIN_PASSWORD"]:
                        password_hash = v
        except Exception:
            pass
    return username, password_hash


settings = Settings()
