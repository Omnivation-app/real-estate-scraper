"""
Module principal de scraping pour les annonces immobilières.

Responsabilités :
- Identifier les agences immobilières pour un code postal
- Récupérer les annonces de chaque agence
- Respecter les contraintes légales
"""

import logging
import asyncio
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.scraper.legal import legal_compliance, rgpd_compliance
from app.scraper.parser import RealEstateParser

logger = logging.getLogger(__name__)

# User-Agent pour les requêtes
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class RealEstateScraper:
    """Scraper pour les annonces immobilières."""

    def __init__(self):
        """Initialiser le scraper."""
        self.session = self._create_session()
        self.agencies_found: Dict[str, dict] = {}

    def _create_session(self) -> requests.Session:
        """
        Créer une session requests avec retry strategy.
        
        Returns:
            Session configurée
        """
        session = requests.Session()
        
        # Configurer les retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Définir le User-Agent
        session.headers.update({"User-Agent": USER_AGENT})
        
        return session

    def find_agencies_by_postal_code(self, postal_code: str) -> List[Dict]:
        """
        Identifier les agences immobilières pour un code postal.
        
        IMPORTANT : Cette fonction utilise des recherches web simples.
        Pour une production, utiliser des annuaires professionnels (FNAIM, etc.)
        ou des APIs dédiées.
        
        Args:
            postal_code: Code postal français (5 chiffres)
            
        Returns:
            Liste des agences trouvées
        """
        logger.info(f"Searching for agencies in postal code {postal_code}")
        
        agencies = []
        
        # Exemple : chercher des agences connues
        # En production, utiliser une base de données d'agences ou une API
        known_agencies = [
            {
                "name": "SeLoger",
                "website": "https://www.seloger.com",
                "search_url": f"https://www.seloger.com/list.htm?cp={postal_code}",
            },
            {
                "name": "LeBonCoin",
                "website": "https://www.leboncoin.fr",
                "search_url": f"https://www.leboncoin.fr/search?category=9&locations={postal_code}",
            },
            {
                "name": "Immobilier.com",
                "website": "https://www.immobilier.com",
                "search_url": f"https://www.immobilier.com/recherche/vente?cp={postal_code}",
            },
        ]
        
        for agency in known_agencies:
            domain = urlparse(agency["website"]).netloc
            
            # Vérifier si le scraping est autorisé
            can_scrape, reason = legal_compliance.can_scrape(agency["search_url"], USER_AGENT)
            if not can_scrape:
                logger.warning(f"Cannot scrape {domain}: {reason}")
                continue
            
            agencies.append(agency)
        
        return agencies

    def scrape_agency_listings(self, agency_url: str, postal_code: str) -> List[Dict]:
        """
        Récupérer les annonces d'une agence pour un code postal.
        
        Args:
            agency_url: URL de l'agence
            postal_code: Code postal
            
        Returns:
            Liste des annonces
        """
        domain = urlparse(agency_url).netloc
        
        # Vérifier les autorisations
        can_scrape, reason = legal_compliance.can_scrape(agency_url, USER_AGENT)
        if not can_scrape:
            logger.error(f"Cannot scrape {agency_url}: {reason}")
            return []
        
        # Appliquer le throttling
        legal_compliance.wait_before_request(domain)
        
        listings = []
        
        try:
            # Récupérer la page
            response = self.session.get(agency_url, timeout=10)
            response.raise_for_status()
            
            # Parser les annonces
            parser = RealEstateParser(agency_url)
            listings = parser.extract_listings(response.text)
            
            logger.info(f"Found {len(listings)} listings from {domain}")
            
        except requests.exceptions.RequestException as e:
            status_code = getattr(e.response, "status_code", 0) if hasattr(e, "response") else 0
            error_msg = str(e)
            
            logger.error(f"Error scraping {agency_url}: {error_msg} (status: {status_code})")
            legal_compliance.handle_error(domain, status_code, error_msg)
        
        return listings

    def scrape_agency_info(self, agency_website: str) -> Dict:
        """
        Récupérer les informations légales d'une agence.
        
        Cherche les pages "Mentions légales", "Qui sommes-nous", "Contact", etc.
        
        Args:
            agency_website: URL du site de l'agence
            
        Returns:
            Dict avec les informations extraites
        """
        domain = urlparse(agency_website).netloc
        
        # Pages possibles pour les mentions légales
        legal_pages = [
            "/mentions-legales",
            "/mentions_legales",
            "/legal",
            "/about",
            "/qui-sommes-nous",
            "/contact",
            "/agence",
        ]
        
        info = {
            "legal_name": None,
            "postal_address": None,
            "postal_code": None,
            "city": None,
            "phone": None,
            "siren": None,
            "siret": None,
            "professional_card": None,
        }
        
        for page_path in legal_pages:
            url = urljoin(agency_website, page_path)
            
            # Vérifier les autorisations
            can_scrape, _ = legal_compliance.can_scrape(url, USER_AGENT)
            if not can_scrape:
                continue
            
            # Appliquer le throttling
            legal_compliance.wait_before_request(domain)
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    parser = RealEstateParser(agency_website)
                    extracted_info = parser.extract_agency_info(response.text)
                    
                    # Fusionner les informations
                    for key, value in extracted_info.items():
                        if value and not info[key]:
                            info[key] = value
                    
                    logger.debug(f"Extracted agency info from {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.debug(f"Error fetching {url}: {e}")
                continue
        
        return info

    def scrape_postal_code(self, postal_code: str) -> Dict:
        """
        Scraper complet pour un code postal.
        
        Args:
            postal_code: Code postal français
            
        Returns:
            Dict avec agencies et listings
        """
        logger.info(f"Starting scrape for postal code {postal_code}")
        
        result = {
            "postal_code": postal_code,
            "agencies": [],
            "listings": [],
            "total_listings": 0,
            "errors": [],
        }
        
        try:
            # Étape 1 : Trouver les agences
            agencies = self.find_agencies_by_postal_code(postal_code)
            if not agencies:
                result["errors"].append(f"No agencies found for postal code {postal_code}")
                return result
            
            # Étape 2 : Pour chaque agence, récupérer les annonces et les infos légales
            for agency in agencies:
                try:
                    # Récupérer les infos légales
                    agency_info = self.scrape_agency_info(agency["website"])
                    
                    # Récupérer les annonces
                    listings = self.scrape_agency_listings(agency["search_url"], postal_code)
                    
                    # Ajouter les résultats
                    result["agencies"].append({
                        "name": agency["name"],
                        "website": agency["website"],
                        **agency_info,
                        "listings_count": len(listings),
                    })
                    
                    result["listings"].extend(listings)
                    
                except Exception as e:
                    logger.error(f"Error processing agency {agency['name']}: {e}")
                    result["errors"].append(f"Error processing {agency['name']}: {str(e)}")
            
            result["total_listings"] = len(result["listings"])
            logger.info(f"Scrape complete: {result['total_listings']} listings found")
            
        except Exception as e:
            logger.error(f"Error during scrape: {e}")
            result["errors"].append(f"Scrape failed: {str(e)}")
        
        return result
