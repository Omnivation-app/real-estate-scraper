"""
Routes pour les fonctionnalités utilisateur (favoris, alertes, etc.).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.models import User, Favorite, SearchAlert, Listing
from app.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["user"])


# Schémas Pydantic
class FavoriteResponse(BaseModel):
    """Schéma de réponse pour un favori."""
    id: int
    listing_id: int
    created_at: str

    class Config:
        from_attributes = True


class SearchAlertCreate(BaseModel):
    """Schéma de création d'alerte de recherche."""
    name: str
    postal_code: str
    min_price: float = None
    max_price: float = None
    min_surface: float = None
    property_type: str = None


class SearchAlertResponse(BaseModel):
    """Schéma de réponse pour une alerte de recherche."""
    id: int
    name: str
    postal_code: str
    min_price: float = None
    max_price: float = None
    min_surface: float = None
    property_type: str = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


# Routes pour les favoris
@router.get("/favorites", response_model=List[FavoriteResponse])
def get_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Obtenir les favoris de l'utilisateur.

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Liste des favoris
    """
    favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    return favorites


@router.post("/favorites/{listing_id}", response_model=FavoriteResponse)
def add_favorite(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ajouter une annonce aux favoris.

    Args:
        listing_id: ID de l'annonce
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Favori créé

    Raises:
        HTTPException: Si l'annonce n'existe pas ou est déjà en favori
    """
    # Vérifier que l'annonce existe
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    # Vérifier que ce n'est pas déjà en favori
    existing_favorite = db.query(Favorite).filter(
        (Favorite.user_id == current_user.id) & (Favorite.listing_id == listing_id)
    ).first()

    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing already in favorites",
        )

    # Créer le favori
    favorite = Favorite(user_id=current_user.id, listing_id=listing_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


@router.delete("/favorites/{listing_id}")
def remove_favorite(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Supprimer une annonce des favoris.

    Args:
        listing_id: ID de l'annonce
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Message de confirmation

    Raises:
        HTTPException: Si le favori n'existe pas
    """
    favorite = db.query(Favorite).filter(
        (Favorite.user_id == current_user.id) & (Favorite.listing_id == listing_id)
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )

    db.delete(favorite)
    db.commit()

    return {"message": "Favorite removed successfully"}


# Routes pour les alertes de recherche
@router.get("/alerts", response_model=List[SearchAlertResponse])
def get_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Obtenir les alertes de recherche de l'utilisateur.

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Liste des alertes
    """
    alerts = db.query(SearchAlert).filter(SearchAlert.user_id == current_user.id).all()
    return alerts


@router.post("/alerts", response_model=SearchAlertResponse)
def create_alert(
    alert_data: SearchAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Créer une nouvelle alerte de recherche.

    Args:
        alert_data: Données de l'alerte
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Alerte créée
    """
    alert = SearchAlert(
        user_id=current_user.id,
        name=alert_data.name,
        postal_code=alert_data.postal_code,
        min_price=alert_data.min_price,
        max_price=alert_data.max_price,
        min_surface=alert_data.min_surface,
        property_type=alert_data.property_type,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


@router.put("/alerts/{alert_id}", response_model=SearchAlertResponse)
def update_alert(
    alert_id: int,
    alert_data: SearchAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mettre à jour une alerte de recherche.

    Args:
        alert_id: ID de l'alerte
        alert_data: Nouvelles données
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Alerte mise à jour

    Raises:
        HTTPException: Si l'alerte n'existe pas ou n'appartient pas à l'utilisateur
    """
    alert = db.query(SearchAlert).filter(
        (SearchAlert.id == alert_id) & (SearchAlert.user_id == current_user.id)
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    alert.name = alert_data.name
    alert.postal_code = alert_data.postal_code
    alert.min_price = alert_data.min_price
    alert.max_price = alert_data.max_price
    alert.min_surface = alert_data.min_surface
    alert.property_type = alert_data.property_type

    db.commit()
    db.refresh(alert)

    return alert


@router.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Supprimer une alerte de recherche.

    Args:
        alert_id: ID de l'alerte
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Message de confirmation

    Raises:
        HTTPException: Si l'alerte n'existe pas ou n'appartient pas à l'utilisateur
    """
    alert = db.query(SearchAlert).filter(
        (SearchAlert.id == alert_id) & (SearchAlert.user_id == current_user.id)
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    db.delete(alert)
    db.commit()

    return {"message": "Alert deleted successfully"}


@router.post("/alerts/{alert_id}/toggle")
def toggle_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Activer/désactiver une alerte de recherche.

    Args:
        alert_id: ID de l'alerte
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Alerte mise à jour

    Raises:
        HTTPException: Si l'alerte n'existe pas ou n'appartient pas à l'utilisateur
    """
    alert = db.query(SearchAlert).filter(
        (SearchAlert.id == alert_id) & (SearchAlert.user_id == current_user.id)
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    alert.is_active = not alert.is_active
    db.commit()
    db.refresh(alert)

    return alert
