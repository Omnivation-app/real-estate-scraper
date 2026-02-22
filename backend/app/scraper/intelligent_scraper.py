"""
Scraper intelligent capable de s'adapter à n'importe quel site d'agence
"""

import asyncio
import logging
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

logger = logging.getLogger(__name__)


class FormatDetector:
    """Détecte automatiquement le format des annonces"""
    
    PLATFORM_PATTERNS = {
        "wordpress": {
            "indicators": ["wp-content", "wp-includes", "wp-json"],
            "selectors": [".post", ".property", ".listing", ".product", "[data-post-id]"]
        },
        "wix": {
            "indicators": ["wix.com", "wixstatic.com", "wix-data"],
            "selectors": ["[data-mesh-id]", ".wixui", "[data-testid]"]
        },
        "shopify": {
            "indicators": ["shopify.com", "cdn.shopify.com", "myshopify"],
            "selectors": [".product", ".listing", "[data-product-id]"]
        },
        "joomla": {
            "indicators": ["joomla", "component_", "Joomla"],
            "selectors": [".item", ".article", "[data-item-id]"]
        },
        "drupal": {
            "indicators": ["drupal", "sites/default", "sites/all"],
            "selectors": [".node", ".entity", "[data-entity-id]"]
        },
        "custom": {
            "indicators": [],
            "selectors": [".bien", ".annonce", ".property", ".listing", "[data-listing]"]
        }
    }
    
    async def detect_format(self, url: str, html: str) -> Dict:
        """
        Détecte le format du site
        
        Args:
            url: URL du site
            html: Contenu HTML
        
        Returns:
            Dictionnaire avec le format détecté et les sélecteurs
        """
        
        # 1. Vérifier les indicateurs de plateforme
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            if self._check_indicators(html, url, patterns["indicators"]):
                return {
                    "platform": platform,
                    "selectors": patterns["selectors"],
                    "confidence": 0.9
                }
        
        # 2. Analyser la structure HTML
        structure = self._analyze_structure(html)
        
        # 3. Générer les sélecteurs dynamiquement
        selectors = self._generate_selectors(structure)
        
        return {
            "platform": "custom",
            "selectors": selectors,
            "structure": structure,
            "confidence": 0.5
        }
    
    @staticmethod
    def _check_indicators(html: str, url: str, indicators: List[str]) -> bool:
        """Vérifie si les indicateurs sont présents"""
        content = (html + url).lower()
        return any(indicator.lower() in content for indicator in indicators)
    
    @staticmethod
    def _analyze_structure(html: str) -> Dict:
        """Analyse la structure HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Chercher les patterns courants
        structure = {
            "has_data_attributes": bool(soup.find(attrs={"data-": True})),
            "has_microdata": bool(soup.find(attrs={"itemtype": True})),
            "has_json_ld": bool(soup.find("script", {"type": "application/ld+json"})),
            "common_classes": [],
            "common_ids": []
        }
        
        # Récupérer les classes et IDs courants
        for tag in soup.find_all():
            if tag.get("class"):
                structure["common_classes"].extend(tag.get("class", []))
            if tag.get("id"):
                structure["common_ids"].append(tag.get("id"))
        
        return structure
    
    @staticmethod
    def _generate_selectors(structure: Dict) -> List[str]:
        """Génère les sélecteurs CSS"""
        selectors = []
        
        # Mots-clés courants pour les annonces immobilières
        keywords = [
            "annonce", "bien", "property", "listing", "offer",
            "immobilier", "immo", "logement", "appartement", "maison",
            "item", "product", "card", "article"
        ]
        
        for keyword in keywords:
            # Classes
            selectors.append(f".{keyword}")
            selectors.append(f"[class*='{keyword}']")
            
            # IDs
            selectors.append(f"#{keyword}")
            selectors.append(f"[id*='{keyword}']")
            
            # Data attributes
            selectors.append(f"[data-{keyword}]")
            selectors.append(f"[data*='{keyword}']")
        
        return selectors


class DynamicParser:
    """Parser dynamique pour extraire les annonces"""
    
    FIELD_PATTERNS = {
        "title": [
            "h1", "h2", ".title", ".name", ".heading",
            "[data-title]", "[data-name]", "[itemprop='name']"
        ],
        "price": [
            ".price", ".montant", ".cost", ".amount",
            "[data-price]", "[itemprop='price']",
            "span:contains('€')", "span:contains('€')"
        ],
        "surface": [
            ".surface", ".m2", ".sqm", ".area",
            "[data-surface]", "[itemprop='floorSize']"
        ],
        "rooms": [
            ".rooms", ".pieces", ".bedrooms", ".beds",
            "[data-rooms]", "[itemprop='numberOfRooms']"
        ],
        "description": [
            ".description", ".details", ".content", "p",
            "[data-description]", "[itemprop='description']"
        ],
        "images": [
            "img", ".image", ".photo", ".gallery",
            "[data-image]", "[itemprop='image']"
        ],
        "address": [
            ".address", ".location", ".place",
            "[data-address]", "[itemprop='address']"
        ],
        "contact": [
            ".contact", ".agent", ".phone",
            "[data-contact]", "[data-agent]"
        ]
    }
    
    async def parse_listings(self, html: str, selectors: List[str]) -> List[Dict]:
        """
        Parse les annonces
        
        Args:
            html: Contenu HTML
            selectors: Sélecteurs CSS pour les annonces
        
        Returns:
            Liste des annonces extraites
        """
        listings = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Trouver les éléments annonces
        listing_elements = []
        for selector in selectors:
            try:
                listing_elements.extend(soup.select(selector))
            except:
                continue
        
        # Dédupliquer
        listing_elements = list(set(listing_elements))
        
        # Parser chaque annonce
        for element in listing_elements:
            listing = self._extract_listing(element)
            if listing and self._is_valid_listing(listing):
                listings.append(listing)
        
        return listings
    
    def _extract_listing(self, element) -> Optional[Dict]:
        """Extrait les données d'une annonce"""
        listing = {}
        
        for field, patterns in self.FIELD_PATTERNS.items():
            for pattern in patterns:
                try:
                    # Essayer le sélecteur CSS
                    value_elem = element.select_one(pattern)
                    
                    if value_elem:
                        value = value_elem.get_text(strip=True)
                        
                        # Nettoyer la valeur
                        value = self._clean_value(value, field)
                        
                        if value:
                            listing[field] = value
                            break
                except:
                    continue
        
        return listing if listing else None
    
    @staticmethod
    def _clean_value(value: str, field: str) -> Optional[str]:
        """Nettoie et normalise la valeur"""
        if not value:
            return None
        
        # Supprimer les espaces inutiles
        value = " ".join(value.split())
        
        # Champs spécifiques
        if field == "price":
            # Extraire les chiffres
            numbers = re.findall(r'\d+(?:\s*\d+)*', value.replace(" ", ""))
            return numbers[0] if numbers else None
        
        elif field == "surface":
            # Extraire les chiffres
            numbers = re.findall(r'\d+', value)
            return numbers[0] if numbers else None
        
        elif field == "rooms":
            # Extraire les chiffres
            numbers = re.findall(r'\d+', value)
            return numbers[0] if numbers else None
        
        return value
    
    @staticmethod
    def _is_valid_listing(listing: Dict) -> bool:
        """Vérifie si l'annonce est valide"""
        # Au minimum, doit avoir un titre et un prix
        return bool(listing.get("title") and listing.get("price"))


class ProxyRotation:
    """Gère la rotation des proxies"""
    
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.current_index = 0
    
    def get_proxy(self) -> Optional[str]:
        """Récupère le prochain proxy"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy


class IntelligentScraper:
    """Scraper intelligent multi-domaines"""
    
    def __init__(self, proxies: List[str] = None):
        self.format_detector = FormatDetector()
        self.parser = DynamicParser()
        self.proxy_manager = ProxyRotation(proxies)
        self.session = None
    
    async def scrape_agency(self, agency_url: str, use_selenium: bool = False) -> List[Dict]:
        """
        Scrape une agence
        
        Args:
            agency_url: URL de l'agence
            use_selenium: Utiliser Selenium pour les sites JavaScript
        
        Returns:
            Liste des annonces
        """
        
        try:
            # 1. Récupérer le contenu HTML
            if use_selenium:
                html = await self._fetch_with_selenium(agency_url)
            else:
                html = await self._fetch_with_aiohttp(agency_url)
            
            if not html:
                logger.warning(f"Impossible de récupérer {agency_url}")
                return []
            
            # 2. Détecter le format
            format_info = await self.format_detector.detect_format(agency_url, html)
            logger.info(f"Format détecté: {format_info['platform']} (confiance: {format_info['confidence']})")
            
            # 3. Parser les annonces
            listings = await self.parser.parse_listings(html, format_info["selectors"])
            
            logger.info(f"Trouvé {len(listings)} annonces sur {agency_url}")
            
            return listings
            
        except Exception as e:
            logger.error(f"Erreur scraping {agency_url}: {e}")
            return []
    
    async def _fetch_with_aiohttp(self, url: str) -> Optional[str]:
        """Récupère le contenu avec aiohttp"""
        try:
            proxy = self.proxy_manager.get_proxy()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    proxy=proxy,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Status {response.status} pour {url}")
                        return None
        
        except Exception as e:
            logger.error(f"Erreur aiohttp {url}: {e}")
            return None
    
    async def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """Récupère le contenu avec Selenium (pour sites JavaScript)"""
        driver = None
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Ajouter proxy si disponible
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                options.add_argument(f'--proxy-server={proxy}')
            
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            
            # Attendre le chargement
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )
            
            # Attendre les annonces
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "listing"))
                )
            except:
                pass  # Les annonces peuvent ne pas être présentes
            
            return driver.page_source
            
        except Exception as e:
            logger.error(f"Erreur Selenium {url}: {e}")
            return None
        
        finally:
            if driver:
                driver.quit()
    
    async def scrape_multiple_agencies(self, agencies: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Scrape plusieurs agences en parallèle
        
        Args:
            agencies: Liste des agences à scraper
        
        Returns:
            Dictionnaire {url: listings}
        """
        
        results = {}
        
        # Créer les tâches
        tasks = []
        for agency in agencies:
            url = agency.get('website_url')
            if url:
                tasks.append(self.scrape_agency(url))
        
        # Exécuter en parallèle
        listings_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Associer les résultats aux agences
        for i, agency in enumerate(agencies):
            url = agency.get('website_url')
            if url and i < len(listings_results):
                result = listings_results[i]
                if isinstance(result, list):
                    results[url] = result
                else:
                    logger.error(f"Erreur scraping {url}: {result}")
        
        return results


class ListingDeduplicator:
    """Déduplique les annonces"""
    
    @staticmethod
    def generate_hash(listing: Dict) -> str:
        """Génère un hash unique pour une annonce"""
        
        # Créer une signature basée sur les données clés
        signature = f"{listing.get('title', '')}|{listing.get('price', '')}|{listing.get('address', '')}"
        
        # Normaliser
        signature = signature.lower().strip()
        
        # Supprimer les espaces
        signature = re.sub(r'\s+', ' ', signature)
        
        # Hash SHA256
        return hashlib.sha256(signature.encode()).hexdigest()
    
    @staticmethod
    def are_duplicates(listing1: Dict, listing2: Dict, threshold: float = 0.8) -> bool:
        """Vérifie si deux annonces sont des doublons"""
        
        # Comparer les champs clés
        title_match = listing1.get('title', '').lower() == listing2.get('title', '').lower()
        price_match = listing1.get('price', '') == listing2.get('price', '')
        address_match = listing1.get('address', '').lower() == listing2.get('address', '').lower()
        
        # Si au moins 2 champs correspondent, c'est un doublon
        matches = sum([title_match, price_match, address_match])
        
        return matches >= 2
