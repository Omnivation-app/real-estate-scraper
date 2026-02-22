"""
Routes API pour la découverte et le scraping décentralisé
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.database import get_db
from app.models_decentralized import (
    Agency, AggregatedListing, ScrapingLog, MarketStatistics
)
from app.scraper.agency_discovery import AgencyDiscoveryEngine
from app.scraper.intelligent_scraper import IntelligentScraper
from app.scraper.continuous_scraping import ContinuousScrapingEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


# ==================== DISCOVERY ROUTES ====================

@router.post("/discover-agencies/{postal_code}")
async def discover_agencies(
    postal_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Découvrir les agences pour un code postal
    
    Args:
        postal_code: Code postal (ex: "75015")
    
    Returns:
        Liste des agences découvertes
    """
    
    try:
        # Initialiser le moteur de découverte
        engine = AgencyDiscoveryEngine(api_key="your_google_maps_api_key")
        
        # Découvrir les agences
        agencies = await engine.discover_all_agencies(postal_code, "Paris")
        
        # Sauvegarder dans la base de données
        saved_count = 0
        for agency_data in agencies:
            try:
                # Vérifier si l'agence existe
                existing = db.query(Agency).filter(
                    Agency.website_url == agency_data.get('website_url')
                ).first()
                
                if not existing:
                    # Créer une nouvelle agence
                    agency = Agency(
                        name=agency_data.get('name'),
                        website_url=agency_data.get('website_url'),
                        phone=agency_data.get('phone'),
                        address=agency_data.get('address'),
                        postal_code=postal_code,
                        city=agency_data.get('city', 'Paris'),
                        latitude=agency_data.get('latitude'),
                        longitude=agency_data.get('longitude'),
                        discovered_from=agency_data.get('discovered_from', []),
                        scraping_status="pending",
                        is_active=True
                    )
                    db.add(agency)
                    saved_count += 1
                else:
                    # Mettre à jour les sources
                    existing.discovered_from.extend(agency_data.get('discovered_from', []))
                    existing.discovered_from = list(set(existing.discovered_from))
            
            except Exception as e:
                logger.error(f"Erreur sauvegarde agence: {e}")
                continue
        
        db.commit()
        
        # Lancer le scraping en arrière-plan
        background_tasks.add_task(
            scrape_discovered_agencies,
            postal_code,
            db
        )
        
        return {
            "status": "success",
            "postal_code": postal_code,
            "agencies_discovered": len(agencies),
            "agencies_saved": saved_count,
            "message": f"Découverte terminée. {saved_count} agences sauvegardées. Scraping lancé en arrière-plan."
        }
    
    except Exception as e:
        logger.error(f"Erreur découverte: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agencies")
async def get_agencies(
    postal_code: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    Récupérer les agences
    
    Query params:
        postal_code: Filtrer par code postal
        city: Filtrer par ville
        status: Filtrer par statut (pending, active, success, failed, blocked)
        limit: Nombre de résultats
        offset: Décalage
    """
    
    try:
        query = db.query(Agency).filter(Agency.is_active == True)
        
        if postal_code:
            query = query.filter(Agency.postal_code == postal_code)
        
        if city:
            query = query.filter(Agency.city.ilike(f"%{city}%"))
        
        if status:
            query = query.filter(Agency.scraping_status == status)
        
        total = query.count()
        agencies = query.limit(limit).offset(offset).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "agencies": [
                {
                    "id": a.id,
                    "name": a.name,
                    "website_url": a.website_url,
                    "phone": a.phone,
                    "address": a.address,
                    "postal_code": a.postal_code,
                    "city": a.city,
                    "scraping_status": a.scraping_status,
                    "total_listings": a.total_listings,
                    "active_listings": a.active_listings,
                    "last_scraped": a.last_scraped,
                    "discovered_from": a.discovered_from
                }
                for a in agencies
            ]
        }
    
    except Exception as e:
        logger.error(f"Erreur récupération agences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agencies/{agency_id}")
async def get_agency(agency_id: int, db: Session = Depends(get_db)):
    """Récupérer une agence par ID"""
    
    try:
        agency = db.query(Agency).filter(Agency.id == agency_id).first()
        
        if not agency:
            raise HTTPException(status_code=404, detail="Agence non trouvée")
        
        return {
            "id": agency.id,
            "name": agency.name,
            "website_url": agency.website_url,
            "phone": agency.phone,
            "email": agency.email,
            "address": agency.address,
            "postal_code": agency.postal_code,
            "city": agency.city,
            "latitude": agency.latitude,
            "longitude": agency.longitude,
            "siren": agency.siren,
            "siret": agency.siret,
            "scraping_status": agency.scraping_status,
            "total_listings": agency.total_listings,
            "active_listings": agency.active_listings,
            "last_scraped": agency.last_scraped,
            "discovered_from": agency.discovered_from,
            "created_at": agency.created_at,
            "updated_at": agency.updated_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération agence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SCRAPING ROUTES ====================

@router.post("/scrape-agency/{agency_id}")
async def scrape_agency(
    agency_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Scraper une agence"""
    
    try:
        agency = db.query(Agency).filter(Agency.id == agency_id).first()
        
        if not agency:
            raise HTTPException(status_code=404, detail="Agence non trouvée")
        
        # Lancer le scraping en arrière-plan
        background_tasks.add_task(
            scrape_agency_background,
            agency_id,
            db
        )
        
        return {
            "status": "scraping_started",
            "agency_id": agency_id,
            "agency_name": agency.name,
            "message": "Scraping lancé en arrière-plan"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape-all")
async def scrape_all(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Scraper toutes les agences"""
    
    try:
        # Compter les agences
        count = db.query(Agency).filter(Agency.is_active == True).count()
        
        # Lancer le scraping en arrière-plan
        background_tasks.add_task(scrape_all_background, db)
        
        return {
            "status": "scraping_started",
            "agencies_count": count,
            "message": f"Scraping de {count} agences lancé en arrière-plan"
        }
    
    except Exception as e:
        logger.error(f"Erreur scraping global: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scraping-logs/{agency_id}")
async def get_scraping_logs(
    agency_id: int,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    """Récupérer les logs de scraping d'une agence"""
    
    try:
        logs = db.query(ScrapingLog).filter(
            ScrapingLog.agency_id == agency_id
        ).order_by(ScrapingLog.created_at.desc()).limit(limit).all()
        
        return {
            "agency_id": agency_id,
            "logs": [
                {
                    "id": log.id,
                    "status": log.status,
                    "listings_found": log.listings_found,
                    "listings_new": log.listings_new,
                    "listings_updated": log.listings_updated,
                    "listings_removed": log.listings_removed,
                    "duration_seconds": log.duration_seconds,
                    "error_message": log.error_message,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }
    
    except Exception as e:
        logger.error(f"Erreur récupération logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LISTINGS ROUTES ====================

@router.get("/listings")
async def get_listings(
    postal_code: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    price_min: Optional[int] = Query(None),
    price_max: Optional[int] = Query(None),
    surface_min: Optional[int] = Query(None),
    surface_max: Optional[int] = Query(None),
    property_type: Optional[str] = Query(None),
    rooms_min: Optional[int] = Query(None),
    rooms_max: Optional[int] = Query(None),
    sort_by: str = Query("price", regex="^(price|surface|updated_at)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    Rechercher les annonces avec filtres avancés
    
    Query params:
        postal_code: Code postal
        city: Ville
        price_min/max: Plage de prix
        surface_min/max: Plage de surface
        property_type: Type de bien
        rooms_min/max: Nombre de pièces
        sort_by: Trier par (price, surface, updated_at)
        order: Ordre (asc, desc)
        limit: Nombre de résultats
        offset: Décalage
    """
    
    try:
        query = db.query(AggregatedListing).filter(AggregatedListing.is_active == True)
        
        # Appliquer les filtres
        if postal_code:
            query = query.filter(AggregatedListing.postal_code == postal_code)
        
        if city:
            query = query.filter(AggregatedListing.city.ilike(f"%{city}%"))
        
        if price_min:
            query = query.filter(AggregatedListing.price >= price_min)
        
        if price_max:
            query = query.filter(AggregatedListing.price <= price_max)
        
        if surface_min:
            query = query.filter(AggregatedListing.surface >= surface_min)
        
        if surface_max:
            query = query.filter(AggregatedListing.surface <= surface_max)
        
        if property_type:
            query = query.filter(AggregatedListing.property_type == property_type)
        
        if rooms_min:
            query = query.filter(AggregatedListing.rooms >= rooms_min)
        
        if rooms_max:
            query = query.filter(AggregatedListing.rooms <= rooms_max)
        
        # Trier
        if sort_by == "price":
            sort_column = AggregatedListing.price
        elif sort_by == "surface":
            sort_column = AggregatedListing.surface
        else:
            sort_column = AggregatedListing.updated_at
        
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        total = query.count()
        listings = query.limit(limit).offset(offset).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "listings": [
                {
                    "id": l.id,
                    "title": l.title,
                    "price": l.price,
                    "price_per_sqm": l.price_per_sqm,
                    "surface": l.surface,
                    "rooms": l.rooms,
                    "bedrooms": l.bedrooms,
                    "bathrooms": l.bathrooms,
                    "property_type": l.property_type,
                    "address": l.address,
                    "postal_code": l.postal_code,
                    "city": l.city,
                    "latitude": l.latitude,
                    "longitude": l.longitude,
                    "agency_id": l.agency_id,
                    "agency_name": l.agency.name if l.agency else None,
                    "source_url": l.source_url,
                    "photos": l.photos,
                    "data_quality_score": l.data_quality_score,
                    "scraped_at": l.scraped_at,
                    "updated_at": l.updated_at
                }
                for l in listings
            ]
        }
    
    except Exception as e:
        logger.error(f"Erreur recherche annonces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listings/{listing_id}")
async def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """Récupérer une annonce par ID"""
    
    try:
        listing = db.query(AggregatedListing).filter(
            AggregatedListing.id == listing_id
        ).first()
        
        if not listing:
            raise HTTPException(status_code=404, detail="Annonce non trouvée")
        
        # Incrémenter le compteur de vues
        listing.view_count += 1
        db.commit()
        
        return {
            "id": listing.id,
            "title": listing.title,
            "description": listing.description,
            "price": listing.price,
            "price_per_sqm": listing.price_per_sqm,
            "surface": listing.surface,
            "rooms": listing.rooms,
            "bedrooms": listing.bedrooms,
            "bathrooms": listing.bathrooms,
            "property_type": listing.property_type,
            "address": listing.address,
            "postal_code": listing.postal_code,
            "city": listing.city,
            "latitude": listing.latitude,
            "longitude": listing.longitude,
            "agency_id": listing.agency_id,
            "agency": {
                "id": listing.agency.id,
                "name": listing.agency.name,
                "phone": listing.agency.phone,
                "email": listing.agency.email,
                "website_url": listing.agency.website_url
            } if listing.agency else None,
            "source_url": listing.source_url,
            "photos": listing.photos,
            "features": listing.features,
            "data_quality_score": listing.data_quality_score,
            "view_count": listing.view_count,
            "favorite_count": listing.favorite_count,
            "scraped_at": listing.scraped_at,
            "updated_at": listing.updated_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération annonce: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ROUTES ====================

@router.get("/statistics/market")
async def get_market_statistics(
    postal_code: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Récupérer les statistiques du marché"""
    
    try:
        query = db.query(MarketStatistics)
        
        if postal_code:
            query = query.filter(MarketStatistics.postal_code == postal_code)
        
        if city:
            query = query.filter(MarketStatistics.city.ilike(f"%{city}%"))
        
        stats = query.order_by(MarketStatistics.updated_at.desc()).all()
        
        return {
            "statistics": [
                {
                    "postal_code": s.postal_code,
                    "city": s.city,
                    "total_listings": s.total_listings,
                    "active_listings": s.active_listings,
                    "average_price": s.average_price,
                    "average_price_per_sqm": s.average_price_per_sqm,
                    "median_price": s.median_price,
                    "price_min": s.price_min,
                    "price_max": s.price_max,
                    "apartments_count": s.apartments_count,
                    "houses_count": s.houses_count,
                    "studios_count": s.studios_count,
                    "listings_added_today": s.listings_added_today,
                    "listings_added_week": s.listings_added_week,
                    "listings_added_month": s.listings_added_month,
                    "updated_at": s.updated_at
                }
                for s in stats
            ]
        }
    
    except Exception as e:
        logger.error(f"Erreur statistiques: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BACKGROUND TASKS ====================

async def scrape_discovered_agencies(postal_code: str, db: Session):
    """Task d'arrière-plan pour scraper les agences découvertes"""
    
    try:
        scraper = IntelligentScraper()
        engine = ContinuousScrapingEngine(db, scraper)
        
        # Récupérer les agences du code postal
        agencies = db.query(Agency).filter(
            Agency.postal_code == postal_code,
            Agency.is_active == True
        ).all()
        
        logger.info(f"Scraping {len(agencies)} agences pour {postal_code}")
        
        for agency in agencies:
            await engine.scrape_agency(agency)
    
    except Exception as e:
        logger.error(f"Erreur scraping arrière-plan: {e}")


async def scrape_agency_background(agency_id: int, db: Session):
    """Task d'arrière-plan pour scraper une agence"""
    
    try:
        agency = db.query(Agency).filter(Agency.id == agency_id).first()
        
        if agency:
            scraper = IntelligentScraper()
            engine = ContinuousScrapingEngine(db, scraper)
            await engine.scrape_agency(agency)
    
    except Exception as e:
        logger.error(f"Erreur scraping agence: {e}")


async def scrape_all_background(db: Session):
    """Task d'arrière-plan pour scraper toutes les agences"""
    
    try:
        scraper = IntelligentScraper()
        engine = ContinuousScrapingEngine(db, scraper)
        await engine.scrape_all_agencies()
    
    except Exception as e:
        logger.error(f"Erreur scraping global: {e}")
