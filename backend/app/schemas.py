"""
Schémas Pydantic pour la validation des données API.
"""

from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PropertyType(str, Enum):
    """Types de biens immobiliers."""
    APARTMENT = "apartment"
    HOUSE = "house"
    LAND = "land"
    COMMERCIAL = "commercial"
    OTHER = "other"


class OperationType(str, Enum):
    """Types d'opération immobilière."""
    SALE = "sale"
    RENTAL = "rental"


# ─── Agency Schemas ───────────────────────────────────────────────────────────

class AgencyBase(BaseModel):
    """Données de base d'une agence."""
    legal_name: str
    website_url: str
    postal_address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    siren: Optional[str] = None
    siret: Optional[str] = None
    professional_card: Optional[str] = None


class AgencyCreate(AgencyBase):
    """Schéma pour créer une agence."""
    pass


class AgencyUpdate(BaseModel):
    """Schéma pour mettre à jour une agence."""
    legal_name: Optional[str] = None
    postal_address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    siren: Optional[str] = None
    siret: Optional[str] = None
    professional_card: Optional[str] = None
    is_active: Optional[bool] = None


class AgencyResponse(AgencyBase):
    """Schéma de réponse pour une agence."""
    id: int
    last_scraped: datetime
    created_at: datetime
    is_active: bool
    listings_count: int = 0

    class Config:
        from_attributes = True


# ─── Listing Schemas ──────────────────────────────────────────────────────────

class ListingBase(BaseModel):
    """Données de base d'une annonce."""
    title: str
    description: Optional[str] = None
    property_type: PropertyType
    operation_type: OperationType
    price: float = Field(..., gt=0)
    surface_area: Optional[float] = Field(None, gt=0)
    number_of_rooms: Optional[int] = Field(None, ge=1)
    number_of_bedrooms: Optional[int] = Field(None, ge=0)
    city: str
    postal_code: str = Field(..., min_length=5, max_length=5)
    district: Optional[str] = None
    address_partial: Optional[str] = None
    listing_url: str
    image_urls: Optional[str] = None
    posted_date: Optional[datetime] = None


class ListingCreate(ListingBase):
    """Schéma pour créer une annonce."""
    agency_id: int
    external_id: str


class ListingUpdate(BaseModel):
    """Schéma pour mettre à jour une annonce."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    surface_area: Optional[float] = Field(None, gt=0)
    number_of_rooms: Optional[int] = Field(None, ge=1)
    number_of_bedrooms: Optional[int] = Field(None, ge=0)
    posted_date: Optional[datetime] = None


class ListingResponse(ListingBase):
    """Schéma de réponse pour une annonce."""
    id: int
    agency_id: int
    external_id: str
    last_updated: datetime
    created_at: datetime
    agency: Optional[AgencyResponse] = None

    class Config:
        from_attributes = True


# ─── Search & Filter Schemas ──────────────────────────────────────────────────

class SearchFilters(BaseModel):
    """Filtres de recherche pour les annonces."""
    postal_code: str = Field(..., min_length=5, max_length=5)
    property_type: Optional[PropertyType] = None
    operation_type: Optional[OperationType] = None
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    surface_min: Optional[float] = Field(None, gt=0)
    surface_max: Optional[float] = Field(None, gt=0)
    agency_id: Optional[int] = None
    city: Optional[str] = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class SearchResponse(BaseModel):
    """Réponse de recherche."""
    total: int
    listings: List[ListingResponse]
    agencies: List[AgencyResponse]
    filters_applied: dict


# ─── Scraping Log Schemas ─────────────────────────────────────────────────────

class ScrapingLogResponse(BaseModel):
    """Schéma de réponse pour un log de scraping."""
    id: int
    domain: str
    status: str
    message: Optional[str] = None
    listings_count: int
    agencies_count: int
    execution_time: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Domain Config Schemas ────────────────────────────────────────────────────

class DomainConfigCreate(BaseModel):
    """Schéma pour créer une configuration de domaine."""
    domain: str
    is_enabled: bool = True
    throttle_delay: float = Field(2.0, ge=0.1)
    max_requests_per_hour: int = Field(100, ge=1)
    respect_robots_txt: bool = True
    notes: Optional[str] = None


class DomainConfigUpdate(BaseModel):
    """Schéma pour mettre à jour une configuration de domaine."""
    is_enabled: Optional[bool] = None
    throttle_delay: Optional[float] = Field(None, ge=0.1)
    max_requests_per_hour: Optional[int] = Field(None, ge=1)
    respect_robots_txt: Optional[bool] = None
    notes: Optional[str] = None


class DomainConfigResponse(BaseModel):
    """Schéma de réponse pour une configuration de domaine."""
    id: int
    domain: str
    is_enabled: bool
    throttle_delay: float
    max_requests_per_hour: int
    respect_robots_txt: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Health & Status Schemas ──────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Réponse de santé de l'API."""
    status: str
    database: str
    timestamp: datetime
