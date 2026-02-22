"""
Module de géolocalisation pour les annonces immobilières.

Utilise Nominatim (OpenStreetMap) pour la géolocalisation gratuite.
"""

import logging
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time

logger = logging.getLogger(__name__)

# Initialiser le géocodeur
geolocator = Nominatim(user_agent="real_estate_scraper")


def geocode_address(address: str, city: str, postal_code: str) -> Optional[Tuple[float, float]]:
    """
    Géolocaliser une adresse.

    Args:
        address: Adresse (partielle ou complète)
        city: Ville
        postal_code: Code postal

    Returns:
        Tuple (latitude, longitude) ou None si échec
    """
    try:
        # Construire l'adresse complète
        full_address = f"{address}, {postal_code} {city}, France"

        # Géolocaliser avec throttling
        time.sleep(1)  # Respecter les limites de Nominatim
        location = geolocator.geocode(full_address, timeout=10)

        if location:
            logger.info(f"Geocoded: {full_address} -> ({location.latitude}, {location.longitude})")
            return (location.latitude, location.longitude)
        else:
            logger.warning(f"Could not geocode: {full_address}")
            return None

    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.error(f"Geocoding error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during geocoding: {str(e)}")
        return None


def geocode_postal_code(postal_code: str, city: str) -> Optional[Tuple[float, float]]:
    """
    Géolocaliser un code postal.

    Args:
        postal_code: Code postal français
        city: Ville

    Returns:
        Tuple (latitude, longitude) ou None si échec
    """
    try:
        full_address = f"{postal_code} {city}, France"
        time.sleep(1)
        location = geolocator.geocode(full_address, timeout=10)

        if location:
            logger.info(f"Geocoded postal code: {full_address} -> ({location.latitude}, {location.longitude})")
            return (location.latitude, location.longitude)
        else:
            logger.warning(f"Could not geocode postal code: {full_address}")
            return None

    except (GeocoderTimedOut, GeocoderUnavailable, Exception) as e:
        logger.error(f"Error geocoding postal code: {str(e)}")
        return None


def calculate_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculer la distance entre deux points (en km).

    Utilise la formule de Haversine.

    Args:
        lat1, lon1: Latitude et longitude du premier point
        lat2, lon2: Latitude et longitude du deuxième point

    Returns:
        Distance en kilomètres
    """
    from math import radians, sin, cos, sqrt, atan2

    R = 6371  # Rayon de la Terre en km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance


def generate_map_html(listings: list, center_lat: float, center_lon: float) -> str:
    """
    Générer une carte HTML interactive avec les annonces.

    Args:
        listings: Liste des annonces avec latitude/longitude
        center_lat: Latitude du centre de la carte
        center_lon: Longitude du centre de la carte

    Returns:
        Code HTML de la carte
    """
    try:
        import folium
        from folium import plugins

        # Créer la carte
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles="OpenStreetMap",
        )

        # Ajouter les marqueurs pour chaque annonce
        for listing in listings:
            if listing.latitude and listing.longitude:
                # Couleur selon le prix
                if listing.price < 200000:
                    color = "green"
                elif listing.price < 500000:
                    color = "blue"
                else:
                    color = "red"

                popup_text = f"""
                <b>{listing.title}</b><br>
                Prix: {listing.price:,.0f}€<br>
                Surface: {listing.surface_area} m²<br>
                <a href="{listing.listing_url}" target="_blank">Voir l'annonce</a>
                """

                folium.Marker(
                    location=[listing.latitude, listing.longitude],
                    popup=folium.Popup(popup_text, max_width=300),
                    icon=folium.Icon(color=color, icon="info-sign"),
                ).add_to(m)

        # Ajouter un contrôle de couches
        folium.LayerControl().add_to(m)

        # Retourner le HTML
        return m._repr_html_()

    except ImportError:
        logger.warning("Folium not installed. Install with: pip install folium")
        return "<p>Folium is required for map generation</p>"
    except Exception as e:
        logger.error(f"Error generating map: {str(e)}")
        return f"<p>Error generating map: {str(e)}</p>"


class GeoLocationService:
    """Service centralisé de géolocalisation."""

    @staticmethod
    def geocode_listing(listing) -> bool:
        """
        Géolocaliser une annonce.

        Args:
            listing: Objet Listing

        Returns:
            True si succès, False sinon
        """
        if listing.latitude and listing.longitude:
            return True  # Déjà géolocalisée

        coords = geocode_address(
            listing.address_partial or listing.city,
            listing.city,
            listing.postal_code,
        )

        if coords:
            listing.latitude, listing.longitude = coords
            return True

        return False

    @staticmethod
    def geocode_agency(agency) -> bool:
        """
        Géolocaliser une agence.

        Args:
            agency: Objet Agency

        Returns:
            True si succès, False sinon
        """
        if agency.latitude and agency.longitude:
            return True  # Déjà géolocalisée

        coords = geocode_address(
            agency.postal_address or agency.city,
            agency.city,
            agency.postal_code,
        )

        if coords:
            agency.latitude, agency.longitude = coords
            return True

        return False

    @staticmethod
    def find_nearby_listings(
        listings: list, center_lat: float, center_lon: float, radius_km: float = 5
    ) -> list:
        """
        Trouver les annonces à proximité.

        Args:
            listings: Liste des annonces
            center_lat: Latitude du centre
            center_lon: Longitude du centre
            radius_km: Rayon de recherche en km

        Returns:
            Liste des annonces à proximité
        """
        nearby = []

        for listing in listings:
            if listing.latitude and listing.longitude:
                distance = calculate_distance(
                    center_lat, center_lon, listing.latitude, listing.longitude
                )

                if distance <= radius_km:
                    nearby.append((listing, distance))

        # Trier par distance
        nearby.sort(key=lambda x: x[1])
        return [listing for listing, _ in nearby]


# Instance globale
geo_service = GeoLocationService()
