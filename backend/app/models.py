"""
Modèles SQLAlchemy pour la base de données immobilière.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class PropertyType(str, enum.Enum):
    """Types de biens immobiliers."""
    APARTMENT = "apartment"
    HOUSE = "house"
    LAND = "land"
    COMMERCIAL = "commercial"
    OTHER = "other"


class OperationType(str, enum.Enum):
    """Types d'opération immobilière."""
    SALE = "sale"
    RENTAL = "rental"


class Agency(Base):
    """Modèle pour une agence immobilière."""
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    # Informations légales
    legal_name = Column(String(255), nullable=False)
    website_url = Column(String(500), unique=True, nullable=False, index=True)
    postal_address = Column(String(500), nullable=True)
    postal_code = Column(String(5), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    siren = Column(String(14), nullable=True, unique=True)
    siret = Column(String(14), nullable=True, unique=True)
    professional_card = Column(String(50), nullable=True)
    
    # Métadonnées
    last_scraped = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    source = Column(String(100), nullable=True)  # Source de l'agence
    latitude = Column(Float, nullable=True)  # Pour la géolocalisation
    longitude = Column(Float, nullable=True)  # Pour la géolocalisation
    
    # Relations
    listings = relationship("Listing", back_populates="agency", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Agency(id={self.id}, legal_name='{self.legal_name}', postal_code='{self.postal_code}')>"


class Listing(Base):
    """Modèle pour une annonce immobilière."""
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    # Identifiants
    external_id = Column(String(255), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False, index=True)
    
    # Informations principales
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    property_type = Column(Enum(PropertyType), nullable=False, index=True)
    operation_type = Column(Enum(OperationType), nullable=False, index=True)
    
    # Données immobilières
    price = Column(Float, nullable=False, index=True)
    surface_area = Column(Float, nullable=True)  # m²
    number_of_rooms = Column(Integer, nullable=True)
    number_of_bedrooms = Column(Integer, nullable=True)
    
    # Localisation
    city = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(5), nullable=False, index=True)
    district = Column(String(100), nullable=True)
    address_partial = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)  # Pour la géolocalisation
    longitude = Column(Float, nullable=True)  # Pour la géolocalisation
    
    # URLs et métadonnées
    listing_url = Column(String(500), nullable=False, unique=True)
    image_urls = Column(Text, nullable=True)  # JSON array as string
    source = Column(String(100), nullable=True)  # Source de l'annonce
    
    # Dates
    posted_date = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    agency = relationship("Agency", back_populates="listings")

    def __repr__(self):
        return f"<Listing(id={self.id}, title='{self.title}', price={self.price}, postal_code='{self.postal_code}')>"


class ScrapingLog(Base):
    """Modèle pour tracer les opérations de scraping."""
    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # "success", "error", "blocked", "throttled"
    message = Column(Text, nullable=True)
    listings_count = Column(Integer, default=0)
    agencies_count = Column(Integer, default=0)
    execution_time = Column(Float, nullable=True)  # secondes
    source = Column(String(100), nullable=True)  # Source de scraping
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ScrapingLog(id={self.id}, domain='{self.domain}', status='{self.status}')>"


class User(Base):
    """Modèle pour un utilisateur de l'application."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    search_alerts = relationship("SearchAlert", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Favorite(Base):
    """Modèle pour une annonce favorite d'un utilisateur."""
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "listing_id", name="unique_user_listing"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    user = relationship("User", back_populates="favorites")
    listing = relationship("Listing")

    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, listing_id={self.listing_id})>"


class SearchAlert(Base):
    """Modèle pour une alerte de recherche d'un utilisateur."""
    __tablename__ = "search_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    postal_code = Column(String(10), nullable=False)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    min_surface = Column(Float, nullable=True)
    property_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_notified = Column(DateTime, nullable=True)

    # Relations
    user = relationship("User", back_populates="search_alerts")

    def __repr__(self):
        return f"<SearchAlert(id={self.id}, user_id={self.user_id}, name='{self.name}')>"


class DomainConfig(Base):
    """Configuration pour activer/désactiver le scraping par domaine."""
    __tablename__ = "domain_configs"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=True)
    throttle_delay = Column(Float, default=2.0)  # délai en secondes entre requêtes
    max_requests_per_hour = Column(Integer, default=100)
    respect_robots_txt = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DomainConfig(domain='{self.domain}', is_enabled={self.is_enabled})>"


