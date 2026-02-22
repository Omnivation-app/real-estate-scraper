"""
Routes FastAPI pour les annonces immobilières.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models import Listing, Agency
from app.schemas import ListingResponse, SearchFilters, SearchResponse, PropertyType, OperationType

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("/", response_model=SearchResponse)
def search_listings(
    postal_code: str = Query(..., min_length=5, max_length=5),
    property_type: PropertyType = Query(None),
    operation_type: OperationType = Query(None),
    price_min: float = Query(None, ge=0),
    price_max: float = Query(None, ge=0),
    surface_min: float = Query(None, gt=0),
    surface_max: float = Query(None, gt=0),
    agency_id: int = Query(None),
    city: str = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Rechercher les annonces avec filtres.
    
    Query parameters:
    - postal_code: Code postal (obligatoire)
    - property_type: Type de bien (apartment, house, land, commercial, other)
    - operation_type: Type d'opération (sale, rental)
    - price_min/price_max: Fourchette de prix
    - surface_min/surface_max: Fourchette de surface
    - agency_id: Filtrer par agence
    - city: Filtrer par ville
    - limit: Nombre max de résultats (défaut: 50, max: 500)
    - offset: Décalage pour la pagination
    """
    
    # Construire la requête
    query = db.query(Listing).filter(Listing.postal_code == postal_code)
    
    # Appliquer les filtres
    filters_applied = {"postal_code": postal_code}
    
    if property_type:
        query = query.filter(Listing.property_type == property_type)
        filters_applied["property_type"] = property_type
    
    if operation_type:
        query = query.filter(Listing.operation_type == operation_type)
        filters_applied["operation_type"] = operation_type
    
    if price_min is not None:
        query = query.filter(Listing.price >= price_min)
        filters_applied["price_min"] = price_min
    
    if price_max is not None:
        query = query.filter(Listing.price <= price_max)
        filters_applied["price_max"] = price_max
    
    if surface_min is not None:
        query = query.filter(Listing.surface_area >= surface_min)
        filters_applied["surface_min"] = surface_min
    
    if surface_max is not None:
        query = query.filter(Listing.surface_area <= surface_max)
        filters_applied["surface_max"] = surface_max
    
    if agency_id is not None:
        query = query.filter(Listing.agency_id == agency_id)
        filters_applied["agency_id"] = agency_id
    
    if city:
        query = query.filter(Listing.city.ilike(f"%{city}%"))
        filters_applied["city"] = city
    
    # Compter le total
    total = query.count()
    
    # Appliquer la pagination
    listings = query.offset(offset).limit(limit).all()
    
    # Récupérer les agences uniques
    agency_ids = set(listing.agency_id for listing in listings)
    agencies = db.query(Agency).filter(Agency.id.in_(agency_ids)).all() if agency_ids else []
    
    return SearchResponse(
        total=total,
        listings=listings,
        agencies=agencies,
        filters_applied=filters_applied,
    )


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """Récupérer une annonce par ID."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("/by-postal-code/{postal_code}")
def get_listings_by_postal_code(
    postal_code: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Récupérer toutes les annonces pour un code postal."""
    listings = (
        db.query(Listing)
        .filter(Listing.postal_code == postal_code)
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(Listing).filter(Listing.postal_code == postal_code).count()
    
    return {
        "total": total,
        "postal_code": postal_code,
        "listings": listings,
    }


@router.get("/stats/by-postal-code/{postal_code}")
def get_stats_by_postal_code(postal_code: str, db: Session = Depends(get_db)):
    """Récupérer les statistiques des annonces pour un code postal."""
    listings = db.query(Listing).filter(Listing.postal_code == postal_code).all()
    
    if not listings:
        return {
            "postal_code": postal_code,
            "total_listings": 0,
            "avg_price": None,
            "min_price": None,
            "max_price": None,
            "avg_surface": None,
            "property_types": {},
            "operation_types": {},
        }
    
    prices = [l.price for l in listings if l.price]
    surfaces = [l.surface_area for l in listings if l.surface_area]
    
    property_types = {}
    operation_types = {}
    
    for listing in listings:
        property_types[listing.property_type] = property_types.get(listing.property_type, 0) + 1
        operation_types[listing.operation_type] = operation_types.get(listing.operation_type, 0) + 1
    
    return {
        "postal_code": postal_code,
        "total_listings": len(listings),
        "avg_price": sum(prices) / len(prices) if prices else None,
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "avg_surface": sum(surfaces) / len(surfaces) if surfaces else None,
        "property_types": property_types,
        "operation_types": operation_types,
    }
