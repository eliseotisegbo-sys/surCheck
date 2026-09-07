"""Configuration globale de l'API SûrCheck AI."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "SûrCheck AI API"
    VERSION: str = "v1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://surcheck.bj",
        "https://surcheck-ai.vercel.app",
    ]

    # Sécurité & Hachage des numéros
    PHONE_HASH_SALT: str = os.getenv(
        "PHONE_HASH_SALT", "surcheck_bj_secure_salt_2026_antigravity_trust"
    )
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "surcheck_jwt_secret_key_production_grade_super_secret"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h

    # Base de données PostgreSQL / Supabase
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/surcheck_dev",
    )

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
