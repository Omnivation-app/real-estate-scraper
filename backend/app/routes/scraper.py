"""
Routes FastAPI pour le scraping des annonces immobilières.
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Agency, Listing, ScrapingLog
from app.scraper import RealEstateScraper
from app.schemas import SearchResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scraper", tags=["scraper"])

# Instance globale du scraper
scraper = RealEstateScraper()


@router.post("/scrape-postal-code/{postal_code}")
def scrape_postal_code(
    postal_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Lancer le scraping pour un code postal.
    
    Cette opération est lancée en arrière-plan et retourne immédiatement.
    Les résultats seront disponibles via l'API de recherche.
    
    IMPORTANT : Respecter les contraintes légales
    - robots.txt est vérifié automatiquement
    - Throttling appliqué
    - RGPD respecté (pas de données personnelles)
    """
    
    # Valider le format du code postal
    if not postal_code.isdigit() or len(postal_code) != 5:
        raise HTTPException(status_code=400, detail="Invalid postal code format")
    
    # Ajouter la tâche de scraping en arrière-plan
    background_tasks.add_task(_scrape_and_save, postal_code, db)
    
    return {
        "status": "scraping_started",
        "postal_code": postal_code,
        "message": "Scraping in progress. Results will be available shortly.",
    }


def _scrape_and_save(postal_code: str, db: Session):
    """
    Effectuer le scraping et sauvegarder les résultats en base de données.
    
    Args:
        postal_code: Code postal
        db: Session de base de données
    """
    try:
        logger.info(f"Starting scrape for postal code {postal_code}")
        
        # Effectuer le scraping
        result = scraper.scrape_postal_code(postal_code)
        
        # Sauvegarder les agences
        for agency_data in result["agencies"]:
            # Vérifier si l'agence existe déjà
            existing = db.query(Agency).filter(
                Agency.website_url == agency_data.get("website")
            ).first()
            
            if not existing:
                agency = Agency(
                    legal_name=agency_data.get("legal_name", "Unknown"),
                    website_url=agency_data.get("website", ""),
                    postal_address=agency_data.get("postal_address"),
                    postal_code=postal_code,
                    city=agency_data.get("city"),
                    phone=agency_data.get("phone"),
                    siren=agency_data.get("siren"),
                    siret=agency_data.get("siret"),
                    professional_card=agency_data.get("professional_card"),
                )
                db.add(agency)
                db.commit()
                db.refresh(agency)
            else:
                agency = existing
        
        # Sauvegarder les annonces
        for listing_data in result["listings"]:
            # Trouver l'agence associée
            agency = db.query(Agency).filter(
                Agency.postal_code == postal_code
            ).first()
            
            if not agency:
                logger.warning(f"No agency found for postal code {postal_code}")
                continue
            
            # Vérifier si l'annonce existe déjà
            existing = db.query(Listing).filter(
                Listing.listing_url == listing_data.get("listing_url")
            ).first()
            
            if not existing:
                listing = Listing(
                    external_id=listing_data.get("listing_url", ""),
                    agency_id=agency.id,
                    title=listing_data.get("title", ""),
                    description=listing_data.get("description"),
                    property_type=listing_data.get("property_type", "other"),
                    operation_type=listing_data.get("operation_type", "sale"),
                    price=listing_data.get("price", 0),
                    surface_area=listing_data.get("surface_area"),
                    number_of_rooms=listing_data.get("number_of_rooms"),
                    number_of_bedrooms=listing_data.get("number_of_bedrooms"),
                    city=listing_data.get("city", ""),
                    postal_code=postal_code,
                    district=listing_data.get("district"),
                    address_partial=listing_data.get("address_partial"),
                    listing_url=listing_data.get("listing_url", ""),
                    image_urls=str(listing_data.get("image_urls", [])),
                    posted_date=listing_data.get("posted_date"),
                )
                db.add(listing)
        
        db.commit()
        
        # Enregistrer le log de scraping
        log = ScrapingLog(
            domain=f"postal_code_{postal_code}",
            status="success",
            message=f"Scraped {len(result['listings'])} listings",
            listings_count=len(result["listings"]),
            agencies_count=len(result["agencies"]),
        )
        db.add(log)
        db.commit()
        
        logger.info(f"Scrape complete for postal code {postal_code}: {len(result['listings'])} listings")
        
    except Exception as e:
        logger.error(f"Error during scrape for postal code {postal_code}: {e}")
        
        # Enregistrer l'erreur
        log = ScrapingLog(
            domain=f"postal_code_{postal_code}",
            status="error",
            message=str(e),
        )
        db.add(log)
        db.commit()


@router.get("/logs")
def get_scraping_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Récupérer les logs de scraping."""
    logs = (
        db.query(ScrapingLog)
        .order_by(ScrapingLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    total = db.query(ScrapingLog).count()
    
    return {
        "total": total,
        "logs": logs,
    }


@router.get("/logs/{domain}")
def get_scraping_logs_by_domain(
    domain: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Récupérer les logs de scraping pour un domaine."""
    logs = (
        db.query(ScrapingLog)
        .filter(ScrapingLog.domain == domain)
        .order_by(ScrapingLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    total = db.query(ScrapingLog).filter(ScrapingLog.domain == domain).count()
    
    return {
        "total": total,
        "domain": domain,
        "logs": logs,
    }
