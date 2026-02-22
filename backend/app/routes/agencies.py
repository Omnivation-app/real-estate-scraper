"""
Routes FastAPI pour les agences immobilières.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Agency, Listing
from app.schemas import AgencyResponse, AgencyCreate, AgencyUpdate

router = APIRouter(prefix="/api/agencies", tags=["agencies"])


@router.get("/", response_model=list[AgencyResponse])
def list_agencies(
    postal_code: str = Query(None),
    is_active: bool = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Lister les agences avec filtres optionnels.
    
    Query parameters:
    - postal_code: Filtrer par code postal
    - is_active: Filtrer par statut actif
    - limit: Nombre max de résultats
    - offset: Décalage pour la pagination
    """
    query = db.query(Agency)
    
    if postal_code:
        query = query.filter(Agency.postal_code == postal_code)
    
    if is_active is not None:
        query = query.filter(Agency.is_active == is_active)
    
    agencies = query.offset(offset).limit(limit).all()
    
    # Ajouter le nombre d'annonces pour chaque agence
    for agency in agencies:
        agency.listings_count = db.query(func.count(Listing.id)).filter(
            Listing.agency_id == agency.id
        ).scalar()
    
    return agencies


@router.get("/{agency_id}", response_model=AgencyResponse)
def get_agency(agency_id: int, db: Session = Depends(get_db)):
    """Récupérer une agence par ID."""
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    
    agency.listings_count = db.query(func.count(Listing.id)).filter(
        Listing.agency_id == agency.id
    ).scalar()
    
    return agency


@router.get("/by-postal-code/{postal_code}", response_model=list[AgencyResponse])
def get_agencies_by_postal_code(postal_code: str, db: Session = Depends(get_db)):
    """Récupérer toutes les agences pour un code postal."""
    agencies = db.query(Agency).filter(Agency.postal_code == postal_code).all()
    
    for agency in agencies:
        agency.listings_count = db.query(func.count(Listing.id)).filter(
            Listing.agency_id == agency.id
        ).scalar()
    
    return agencies


@router.post("/", response_model=AgencyResponse)
def create_agency(agency: AgencyCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle agence."""
    # Vérifier si l'agence existe déjà
    existing = db.query(Agency).filter(Agency.website_url == agency.website_url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agency with this website already exists")
    
    db_agency = Agency(**agency.dict())
    db.add(db_agency)
    db.commit()
    db.refresh(db_agency)
    
    db_agency.listings_count = 0
    return db_agency


@router.put("/{agency_id}", response_model=AgencyResponse)
def update_agency(agency_id: int, agency: AgencyUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une agence."""
    db_agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not db_agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    
    update_data = agency.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_agency, field, value)
    
    db.add(db_agency)
    db.commit()
    db.refresh(db_agency)
    
    db_agency.listings_count = db.query(func.count(Listing.id)).filter(
        Listing.agency_id == agency.id
    ).scalar()
    
    return db_agency


@router.delete("/{agency_id}")
def delete_agency(agency_id: int, db: Session = Depends(get_db)):
    """Supprimer une agence."""
    db_agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not db_agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    
    db.delete(db_agency)
    db.commit()
    
    return {"message": "Agency deleted successfully"}


@router.get("/{agency_id}/listings")
def get_agency_listings(
    agency_id: int,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Récupérer toutes les annonces d'une agence."""
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    
    listings = (
        db.query(Listing)
        .filter(Listing.agency_id == agency_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    total = db.query(func.count(Listing.id)).filter(Listing.agency_id == agency_id).scalar()
    
    return {
        "agency_id": agency_id,
        "agency_name": agency.legal_name,
        "total_listings": total,
        "listings": listings,
    }
