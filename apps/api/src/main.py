"""Point d'entrée principal de l'API SûrCheck AI.
Conforme aux standards de sécurité et d'audit.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import analyze, reports, auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API de prévention et d'évaluation des risques de fraudes numériques pour le Bénin et l'Afrique Francophone.",
    docs_url="/docs",
    redoc_url="/redoc",
)

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


@app.get("/health", tags=["Système"])
@app.get(f"{settings.API_PREFIX}/health", tags=["Système"])
async def healthcheck():
    """Vérification de l'état de l'API et de la version du moteur."""
    return {
        "status": "healthy",
        "engine_version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
