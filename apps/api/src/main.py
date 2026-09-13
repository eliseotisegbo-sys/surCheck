"""Point d'entrée principal de l'API SûrCheck AI.
Conforme aux standards de sécurité, d'audit et de performance (Phase 8).
"""

import os
import sys
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import settings
from .routers import analyze, reports, auth, payment, credits, admin

logger = logging.getLogger("surcheck.startup")


def validate_production_secrets():
    """Valide que tous les secrets critiques sont configurés en production.
    
    Refuse le démarrage si ENVIRONMENT=production et qu'un secret critique est :
    - Vide ("")
    - Égal à une valeur de développement connue
    
    Conforme à la section 1.5 de FIABILISATION_PAIEMENT_SASPAY_SURCHECK_AI.md
    """
    if settings.ENVIRONMENT != "production":
        return  # Validation uniquement en production
    
    errors = []
    
    # Secrets critiques à valider
    critical_secrets = {
        "JWT_SECRET_KEY": settings.JWT_SECRET_KEY,
        "PHONE_HASH_SALT": settings.PHONE_HASH_SALT,
        "DATABASE_URL": settings.DATABASE_URL,
        "SASPAY_API_KEY": settings.SASPAY_API_KEY,
        "SASPAY_WEBHOOK_SECRET": settings.SASPAY_WEBHOOK_SECRET,
    }
    
    # Valeurs de développement interdites en production
    dev_values = {
        "JWT_SECRET_KEY": [
            "",
            "surcheck_jwt_secret_key_development_only_change_in_production",
            "surcheck_jwt_secret_key_production_grade_super_secret_bj",
        ],
        "PHONE_HASH_SALT": [
            "",
            "surcheck_bj_secure_salt_2026_antigravity_trust",
        ],
        "DATABASE_URL": [
            "",
            "postgresql://postgres:postgres@localhost:5432/surcheck_dev",
        ],
        "SASPAY_API_KEY": [""],
        "SASPAY_WEBHOOK_SECRET": [""],
    }
    
    for secret_name, secret_value in critical_secrets.items():
        # Vérifier si vide ou valeur de développement
        if secret_value in dev_values.get(secret_name, []):
            errors.append(
                f"❌ {secret_name} est manquant ou utilise une valeur de développement"
            )
        # Vérifier clés API SasPay (ne doivent pas être en mode test en production)
        elif secret_name == "SASPAY_API_KEY" and secret_value.startswith("sk_test_"):
            errors.append(
                f"⚠️ {secret_name} utilise une clé de test (sk_test_*) en production - utiliser sk_live_*"
            )
    
    if errors:
        logger.error("=" * 80)
        logger.error("🚨 ÉCHEC DE VALIDATION DES SECRETS EN PRODUCTION")
        logger.error("=" * 80)
        for error in errors:
            logger.error(error)
        logger.error("")
        logger.error("L'application refuse de démarrer pour des raisons de sécurité.")
        logger.error("Configurez les variables d'environnement dans Railway/Vercel.")
        logger.error("")
        logger.error("Voir : SECRETS_COMPROMIS_A_REGENERER.md")
        logger.error("=" * 80)
        sys.exit(1)  # Arrêt immédiat
    
    logger.info("✅ Validation des secrets en production : OK")


# Validation des secrets au démarrage (avant création de l'app)
validate_production_secrets()

# Limiteur de débit (désactivé pendant les tests automatisés)
is_testing = os.getenv("TESTING", "0") == "1" or settings.ENVIRONMENT == "test"
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    enabled=not is_testing,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API de prévention et d'évaluation des risques de fraudes numériques pour le Bénin et l'Afrique Francophone.",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
)

# Configuration SlowAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Middleware Headers de Sécurité HTTP
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
    return response

# Configuration CORS pour Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers versionnés
app.include_router(analyze.router, prefix=settings.API_PREFIX)
app.include_router(reports.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(payment.router, prefix=settings.API_PREFIX)
app.include_router(credits.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["Système"])
@app.get(f"{settings.API_PREFIX}/health", tags=["Système"])
async def healthcheck():
    """Vérification de l'état de l'API et de la version du moteur."""
    return {
        "status": "healthy",
        "engine_version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
