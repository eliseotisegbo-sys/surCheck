"""Configuration globale de l'API SûrCheck AI.
Phase 8 — Variables d'environnement validées pour la production.
"""

import os
import json
from typing import Optional
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
        "JWT_SECRET_KEY", "surcheck_jwt_secret_key_development_only_change_in_production"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 jours (7 * 24 * 60 = 10080 minutes)

    # Base de données PostgreSQL / Supabase
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/surcheck_dev",
    )
    SUPABASE_URL: str = os.getenv(
        "SUPABASE_URL",
        "https://lhxbzflectkuysaklvji.supabase.co",
    )
    SUPABASE_ANON_KEY: str = os.getenv(
        "SUPABASE_ANON_KEY",
        "sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH",
    )
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY",
        "",
    )

    # Paiement : Provider sélectionné (chariow | saspay)
    PAYMENT_PROVIDER: str = os.getenv("PAYMENT_PROVIDER", "chariow")

    # Chariow API (Checkout & Pulses/Webhooks)
    CHARIOW_API_KEY: str = os.getenv(
        "CHARIOW_API_KEY", ""
    )
    CHARIOW_BASE_URL: str = os.getenv(
        "CHARIOW_BASE_URL", "https://api.chariow.com/v1"
    )
    CHARIOW_WEBHOOK_SECRET: str = os.getenv("CHARIOW_WEBHOOK_SECRET", "")
    CHARIOW_PRODUCT_PACK_1: str = os.getenv("CHARIOW_PRODUCT_PACK_1", "prd_pack_1")
    CHARIOW_PRODUCT_PACK_5: str = os.getenv("CHARIOW_PRODUCT_PACK_5", "prd_pack_5")
    CHARIOW_PRODUCT_PACK_10: str = os.getenv("CHARIOW_PRODUCT_PACK_10", "prd_pack_10")
    CHARIOW_PRODUCT_PACK_25: str = os.getenv("CHARIOW_PRODUCT_PACK_25", "prd_pack_25")

    # SasPay API (Softpay Mobile Money - Alternatif Chariow)
    SASPAY_API_KEY: str = os.getenv(
        "SASPAY_API_KEY", ""  # sk_test_xxx pour sandbox, sk_live_xxx pour prod
    )
    SASPAY_BASE_URL: str = os.getenv(
        "SASPAY_BASE_URL", "https://api.saspay.me/api/v1"
    )
    SASPAY_WEBHOOK_SECRET: str = os.getenv("SASPAY_WEBHOOK_SECRET", "")

    # Tarifs officiels SûrCheck (minimum Chariow : 565 FCFA)
    CREDIT_PACK_1_FCFA: int = 600      # Analyse unique = 600 FCFA
    CREDIT_PACK_5_FCFA: int = 1500     # 5 analyses = 1 500 FCFA (300 F / unité)
    CREDIT_PACK_10_FCFA: int = 2500    # 10 analyses = 2 500 FCFA (250 F / unité) — Populaire
    CREDIT_PACK_25_FCFA: int = 5000    # 25 analyses = 5 000 FCFA (200 F / unité)

    # URL publique pour redirection post-checkout
    APP_URL: str = os.getenv("APP_URL", "http://localhost:3000")

    model_config = {
        "env_file": ("../../.env", "../.env", ".env"),
        "extra": "allow",
    }

    def model_post_init(self, __context):
        """Parse CORS_ORIGINS depuis l'env si fourni en JSON (format Railway/Vercel)."""
        raw = os.getenv("CORS_ORIGINS")
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    object.__setattr__(self, "CORS_ORIGINS", parsed)
            except (json.JSONDecodeError, TypeError):
                # Format fallback : séparé par des virgules
                object.__setattr__(self, "CORS_ORIGINS", [o.strip() for o in raw.split(",")])


settings = Settings()
