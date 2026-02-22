"""Module de scraping pour les annonces immobilières."""

from app.scraper.scraper import RealEstateScraper
from app.scraper.legal import legal_compliance, rgpd_compliance
from app.scraper.parser import RealEstateParser

__all__ = ["RealEstateScraper", "legal_compliance", "rgpd_compliance", "RealEstateParser"]
