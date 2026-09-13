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
    # ⚠️ AUCUNE valeur par défaut pour les secrets — doit être configuré dans .env
    PHONE_HASH_SALT: str = os.getenv("PHONE_HASH_SALT", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 jours (7 * 24 * 60 = 10080 minutes)

    # Base de données PostgreSQL / Supabase
    # ⚠️ DATABASE_URL ne doit JAMAIS contenir de mot de passe par défaut
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Supabase URL et clés publiques (anon_key est publique, pas sensible)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # ⚠️ Service role key = accès admin complet — JAMAIS de valeur par défaut
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # SasPay API (Softpay Mobile Money - Provider unique)
    # ⚠️ Clés API et webhook secrets ne doivent JAMAIS avoir de valeur par défaut
    SASPAY_API_KEY: str = os.getenv("SASPAY_API_KEY", "")  # sk_test_xxx (sandbox) ou sk_live_xxx (prod)
    SASPAY_BASE_URL: str = os.getenv("SASPAY_BASE_URL", "https://api.saspay.me/api/v1")
    SASPAY_WEBHOOK_SECRET: str = os.getenv("SASPAY_WEBHOOK_SECRET", "")

    # Tarifs officiels SûrCheck (packs de crédits)
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
