"""
Application FastAPI principale pour le scraping immobilier.
"""

import logging
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, init_db
from app.models import Base
from app.schemas import HealthResponse
from app.routes import agencies, listings, scraper, auth, user_features, maps
from app.routes.discovery_scraping import router as discovery_router

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title="Real Estate Scraper API",
    description="API pour scraper les annonces immobilières françaises",
    version="1.0.0",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la base de données
@app.on_event("startup")
async def startup_event():
    """Initialiser la base de données au démarrage."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


# Routes
app.include_router(agencies.router)
app.include_router(listings.router)
app.include_router(scraper.router)
app.include_router(auth.router)
app.include_router(user_features.router)
app.include_router(maps.router)
app.include_router(discovery_router)


# Endpoints de base
@app.get("/", tags=["health"])
def root():
    """Endpoint racine."""
    return {
        "message": "Real Estate Scraper API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check(db: Session = Depends(get_db)):
    """Vérifier la santé de l'API."""
    try:
        # Tester la connexion à la base de données
        db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = "unhealthy"
    
    return HealthResponse(
        status="healthy",
        database=database_status,
        timestamp=datetime.utcnow(),
    )


@app.get("/api/info", tags=["info"])
def get_api_info():
    """Récupérer les informations sur l'API."""
    return {
        "name": "Real Estate Scraper API",
        "version": "1.0.0",
        "description": "API pour scraper les annonces immobilières françaises",
        "endpoints": {
            "agencies": "/api/agencies",
            "listings": "/api/listings",
            "scraper": "/api/scraper",
        },
        "documentation": "/docs",
        "legal_compliance": {
            "robots_txt": "Respecté automatiquement",
            "throttling": "Appliqué par domaine",
            "rgpd": "Pas de données personnelles collectées",
            "rate_limiting": "100 requêtes/heure par domaine",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
