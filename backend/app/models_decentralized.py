"""
Modèles de base de données pour le scraping décentralisé
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib

Base = declarative_base()


class Agency(Base):
    """Modèle pour les agences immobilières"""
    
    __tablename__ = "agencies"
    
    # Identité
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    siren = Column(String(9), unique=True, nullable=True, index=True)
    siret = Column(String(14), unique=True, nullable=True, index=True)
    
    # Contact
    address = Column(String(500), nullable=True)
    postal_code = Column(String(5), index=True, nullable=True)
    city = Column(String(100), index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Web
    website_url = Column(String(1000), unique=True, index=True, nullable=False)
    website_type = Column(String(50), nullable=True)  # "wordpress", "wix", "custom", etc.
    
    # Géolocalisation
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Sources de découverte
    discovered_from = Column(JSON, default=list)  # ["google_maps", "pages_jaunes", ...]
    
    # Scraping
    last_scraped = Column(DateTime, nullable=True)
    scraping_status = Column(String(50), default="pending")  # "pending", "active", "success", "failed", "blocked"
    scraping_error = Column(Text, nullable=True)
    scraping_error_count = Column(Integer, default=0)
    
    # Statistiques
    total_listings = Column(Integer, default=0)
    active_listings = Column(Integer, default=0)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relations
    listings = relationship("AggregatedListing", back_populates="agency", cascade="all, delete-orphan")
    scraping_logs = relationship("ScrapingLog", back_populates="agency", cascade="all, delete-orphan")
    
    # Index composites
    __table_args__ = (
        Index('idx_postal_city', 'postal_code', 'city'),
        Index('idx_status_updated', 'scraping_status', 'updated_at'),
    )


class AggregatedListing(Base):
    """Modèle pour les annonces agrégées"""
    
    __tablename__ = "aggregated_listings"
    
    # Identité
    id = Column(Integer, primary_key=True)
    hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA256 du contenu
    
    # Données de base
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=True, index=True)
    price_per_sqm = Column(Integer, nullable=True)
    
    # Caractéristiques
    property_type = Column(String(50), nullable=True, index=True)  # "apartment", "house", "studio", etc.
    rooms = Column(Integer, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    surface = Column(Integer, nullable=True)
    
    # Localisation
    address = Column(String(500), nullable=True)
    postal_code = Column(String(5), index=True, nullable=True)
    city = Column(String(100), index=True, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Agence source
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False, index=True)
    agency = relationship("Agency", back_populates="listings")
    
    # Métadonnées
    source_url = Column(String(1000), unique=True, nullable=False, index=True)
    photos = Column(JSON, default=list)  # Liste des URLs des photos
    features = Column(JSON, default=dict)  # Caractéristiques additionnelles
    
    # Scraping
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Qualité des données
    data_quality_score = Column(Float, default=0.0)  # 0.0 à 1.0
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(Integer, ForeignKey("aggregated_listings.id"), nullable=True)
    
    # Métadonnées utilisateur
    view_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    
    # Index composites
    __table_args__ = (
        Index('idx_postal_price', 'postal_code', 'price'),
        Index('idx_city_type', 'city', 'property_type'),
        Index('idx_agency_active', 'agency_id', 'is_active'),
        Index('idx_scraped_active', 'scraped_at', 'is_active'),
    )


class ScrapingLog(Base):
    """Modèle pour les logs de scraping"""
    
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Agence
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False, index=True)
    agency = relationship("Agency", back_populates="scraping_logs")
    
    # Résultat
    status = Column(String(50), nullable=False)  # "success", "failed", "blocked", "timeout"
    listings_found = Column(Integer, default=0)
    listings_new = Column(Integer, default=0)
    listings_updated = Column(Integer, default=0)
    listings_removed = Column(Integer, default=0)
    
    # Erreur
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    
    # Performance
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Index
    __table_args__ = (
        Index('idx_agency_created', 'agency_id', 'created_at'),
        Index('idx_status_created', 'status', 'created_at'),
    )


class UserFavorite(Base):
    """Modèle pour les favoris utilisateur"""
    
    __tablename__ = "user_favorites"
    
    id = Column(Integer, primary_key=True)
    
    # Utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Annonce
    listing_id = Column(Integer, ForeignKey("aggregated_listings.id"), nullable=False, index=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Index composites
    __table_args__ = (
        Index('idx_user_listing', 'user_id', 'listing_id', unique=True),
    )


class SearchAlert(Base):
    """Modèle pour les alertes de recherche"""
    
    __tablename__ = "search_alerts"
    
    id = Column(Integer, primary_key=True)
    
    # Utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Critères de recherche
    name = Column(String(255), nullable=False)
    postal_code = Column(String(5), nullable=True)
    city = Column(String(100), nullable=True)
    price_min = Column(Integer, nullable=True)
    price_max = Column(Integer, nullable=True)
    surface_min = Column(Integer, nullable=True)
    surface_max = Column(Integer, nullable=True)
    property_type = Column(String(50), nullable=True)
    rooms_min = Column(Integer, nullable=True)
    rooms_max = Column(Integer, nullable=True)
    
    # Notifications
    notify_by_email = Column(Boolean, default=True)
    notify_by_sms = Column(Boolean, default=False)
    notify_frequency = Column(String(50), default="daily")  # "immediate", "daily", "weekly"
    
    # Métadonnées
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_notified = Column(DateTime, nullable=True)
    
    # Index
    __table_args__ = (
        Index('idx_user_active', 'user_id', 'is_active'),
    )


class ListingHistory(Base):
    """Modèle pour l'historique des annonces"""
    
    __tablename__ = "listing_history"
    
    id = Column(Integer, primary_key=True)
    
    # Annonce
    listing_id = Column(Integer, ForeignKey("aggregated_listings.id"), nullable=False, index=True)
    
    # Changements
    change_type = Column(String(50), nullable=False)  # "created", "updated", "removed"
    previous_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Index
    __table_args__ = (
        Index('idx_listing_created', 'listing_id', 'created_at'),
    )


class User(Base):
    """Modèle pour les utilisateurs"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    
    # Identité
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Authentification
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Profil
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Préférences
    preferences = Column(JSON, default=dict)  # Préférences utilisateur
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class MarketStatistics(Base):
    """Modèle pour les statistiques du marché"""
    
    __tablename__ = "market_statistics"
    
    id = Column(Integer, primary_key=True)
    
    # Localisation
    postal_code = Column(String(5), index=True, nullable=False)
    city = Column(String(100), index=True, nullable=False)
    
    # Statistiques
    total_listings = Column(Integer, default=0)
    active_listings = Column(Integer, default=0)
    average_price = Column(Integer, nullable=True)
    average_price_per_sqm = Column(Integer, nullable=True)
    median_price = Column(Integer, nullable=True)
    price_min = Column(Integer, nullable=True)
    price_max = Column(Integer, nullable=True)
    
    # Par type de bien
    apartments_count = Column(Integer, default=0)
    houses_count = Column(Integer, default=0)
    studios_count = Column(Integer, default=0)
    
    # Tendances
    listings_added_today = Column(Integer, default=0)
    listings_added_week = Column(Integer, default=0)
    listings_added_month = Column(Integer, default=0)
    
    # Métadonnées
    calculated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index
    __table_args__ = (
        Index('idx_postal_updated', 'postal_code', 'updated_at'),
    )


# Fonctions utilitaires

def generate_listing_hash(title: str, price: str, address: str) -> str:
    """Génère un hash unique pour une annonce"""
    signature = f"{title}|{price}|{address}"
    signature = signature.lower().strip()
    return hashlib.sha256(signature.encode()).hexdigest()


def calculate_data_quality_score(listing: AggregatedListing) -> float:
    """Calcule le score de qualité des données"""
    score = 0.0
    max_score = 10.0
    
    # Titre (obligatoire)
    if listing.title:
        score += 2
    
    # Prix (important)
    if listing.price:
        score += 2
    
    # Surface (important)
    if listing.surface:
        score += 2
    
    # Adresse (important)
    if listing.address:
        score += 2
    
    # Description
    if listing.description and len(listing.description) > 50:
        score += 1
    
    # Photos
    if listing.photos and len(listing.photos) > 0:
        score += 1
    
    return score / max_score
