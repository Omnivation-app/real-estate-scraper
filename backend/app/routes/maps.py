"""
Routes pour la géolocalisation et les cartes interactives.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Listing, Agency
from app.geolocation import geo_service, generate_map_html, calculate_distance

router = APIRouter(prefix="/api/maps", tags=["maps"])


@router.get("/listings-map/{postal_code}", response_class=HTMLResponse)
def get_listings_map(postal_code: str, db: Session = Depends(get_db)):
    """
    Obtenir une carte interactive des annonces pour un code postal.

    Args:
        postal_code: Code postal français
        db: Session de base de données

    Returns:
        HTML de la carte Folium
    """
    # Récupérer les annonces
    listings = db.query(Listing).filter(Listing.postal_code == postal_code).all()

    if not listings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No listings found for this postal code",
        )

    # Géolocaliser les annonces sans coordonnées
    for listing in listings:
        if not listing.latitude or not listing.longitude:
            geo_service.geocode_listing(listing)

    # Calculer le centre de la carte
    listings_with_coords = [l for l in listings if l.latitude and l.longitude]

    if not listings_with_coords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not geocode listings",
        )

    center_lat = sum(l.latitude for l in listings_with_coords) / len(listings_with_coords)
    center_lon = sum(l.longitude for l in listings_with_coords) / len(listings_with_coords)

    # Générer la carte
    map_html = generate_map_html(listings_with_coords, center_lat, center_lon)

    return map_html


@router.get("/agencies-map/{postal_code}", response_class=HTMLResponse)
def get_agencies_map(postal_code: str, db: Session = Depends(get_db)):
    """
    Obtenir une carte interactive des agences pour un code postal.

    Args:
        postal_code: Code postal français
        db: Session de base de données

    Returns:
        HTML de la carte Folium
    """
    # Récupérer les agences
    agencies = db.query(Agency).filter(Agency.postal_code == postal_code).all()

    if not agencies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No agencies found for this postal code",
        )

    # Géolocaliser les agences sans coordonnées
    for agency in agencies:
        if not agency.latitude or not agency.longitude:
            geo_service.geocode_agency(agency)

    # Calculer le centre de la carte
    agencies_with_coords = [a for a in agencies if a.latitude and a.longitude]

    if not agencies_with_coords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not geocode agencies",
        )

    center_lat = sum(a.latitude for a in agencies_with_coords) / len(agencies_with_coords)
    center_lon = sum(a.longitude for a in agencies_with_coords) / len(agencies_with_coords)

    # Générer la carte (réutiliser la fonction pour les listings)
    map_html = generate_map_html(agencies_with_coords, center_lat, center_lon)

    return map_html


@router.get("/nearby-listings")
def get_nearby_listings(
    lat: float,
    lon: float,
    radius_km: float = 5,
    db: Session = Depends(get_db),
):
    """
    Obtenir les annonces à proximité d'une coordonnée.

    Args:
        lat: Latitude
        lon: Longitude
        radius_km: Rayon de recherche en km
        db: Session de base de données

    Returns:
        Liste des annonces à proximité
    """
    # Récupérer toutes les annonces avec coordonnées
    listings = db.query(Listing).filter(
        (Listing.latitude != None) & (Listing.longitude != None)
    ).all()

    # Filtrer par distance
    nearby = []
    for listing in listings:
        distance = calculate_distance(lat, lon, listing.latitude, listing.longitude)
        if distance <= radius_km:
            nearby.append({
                "id": listing.id,
                "title": listing.title,
                "price": listing.price,
                "surface_area": listing.surface_area,
                "city": listing.city,
                "postal_code": listing.postal_code,
                "latitude": listing.latitude,
                "longitude": listing.longitude,
                "distance_km": round(distance, 2),
                "listing_url": listing.listing_url,
            })

    # Trier par distance
    nearby.sort(key=lambda x: x["distance_km"])

    return nearby


@router.get("/distance")
def get_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
):
    """
    Calculer la distance entre deux points.

    Args:
        lat1, lon1: Coordonnées du premier point
        lat2, lon2: Coordonnées du deuxième point

    Returns:
        Distance en kilomètres
    """
    distance = calculate_distance(lat1, lon1, lat2, lon2)

    return {
        "distance_km": round(distance, 2),
        "point1": {"latitude": lat1, "longitude": lon1},
        "point2": {"latitude": lat2, "longitude": lon2},
    }
