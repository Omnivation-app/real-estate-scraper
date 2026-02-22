"""
Parser HTML pour extraire les données immobilières.

Logique de parsing pour différents sites d'agences immobilières.
"""

import re
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class RealEstateParser:
    """Parser pour extraire les données immobilières des pages HTML."""

    def __init__(self, base_url: str):
        """
        Initialiser le parser.
        
        Args:
            base_url: URL de base du site
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc

    def extract_agency_info(self, html: str) -> Dict[str, Optional[str]]:
        """
        Extraire les informations légales de l'agence depuis les mentions légales.
        
        Cherche : raison sociale, adresse, SIREN/SIRET, téléphone, etc.
        
        Args:
            html: Contenu HTML de la page "Mentions légales" ou "Qui sommes-nous"
            
        Returns:
            Dict avec les informations extraites
        """
        soup = BeautifulSoup(html, "html.parser")
        
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
        
        # Chercher le texte complet
        text = soup.get_text()
        
        # Extraire SIREN (9 chiffres)
        siren_match = re.search(r"SIREN\s*:?\s*(\d{9})", text, re.IGNORECASE)
        if siren_match:
            info["siren"] = siren_match.group(1)
        
        # Extraire SIRET (14 chiffres)
        siret_match = re.search(r"SIRET\s*:?\s*(\d{14})", text, re.IGNORECASE)
        if siret_match:
            info["siret"] = siret_match.group(1)
        
        # Extraire code postal (5 chiffres)
        postal_match = re.search(r"\b(\d{5})\b", text)
        if postal_match:
            info["postal_code"] = postal_match.group(1)
        
        # Extraire téléphone (format français)
        phone_match = re.search(r"(?:\+33|0)[1-9](?:[0-9]{8})", text)
        if phone_match:
            info["phone"] = phone_match.group(0)
        
        # Extraire le nom de l'agence (généralement en titre ou en gras)
        h1 = soup.find("h1")
        if h1:
            info["legal_name"] = h1.get_text(strip=True)
        
        # Chercher l'adresse (généralement dans un paragraphe)
        for p in soup.find_all("p"):
            text_p = p.get_text(strip=True)
            if len(text_p) > 20 and any(word in text_p.lower() for word in ["rue", "avenue", "boulevard", "place"]):
                info["postal_address"] = text_p
                break
        
        return info

    def extract_listings(self, html: str) -> List[Dict]:
        """
        Extraire les annonces immobilières d'une page de liste.
        
        Args:
            html: Contenu HTML de la page de liste
            
        Returns:
            Liste des annonces extraites
        """
        soup = BeautifulSoup(html, "html.parser")
        listings = []
        
        # Chercher les éléments qui ressemblent à des annonces
        # (divs avec classe "listing", "property", "annonce", etc.)
        listing_selectors = [
            "div.listing", "div.property", "div.annonce",
            "article.listing", "article.property",
            "li.listing", "li.property"
        ]
        
        for selector in listing_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    listing = self._parse_listing_element(element)
                    if listing:
                        listings.append(listing)
                break  # Utiliser le premier sélecteur qui fonctionne
        
        return listings

    def _parse_listing_element(self, element) -> Optional[Dict]:
        """
        Parser un élément d'annonce.
        
        Args:
            element: Élément BeautifulSoup
            
        Returns:
            Dict avec les données de l'annonce ou None
        """
        try:
            listing = {
                "title": None,
                "price": None,
                "surface_area": None,
                "number_of_rooms": None,
                "city": None,
                "postal_code": None,
                "property_type": None,
                "operation_type": None,
                "listing_url": None,
                "description": None,
                "image_urls": [],
            }
            
            # Extraire le titre
            title_elem = element.find(["h2", "h3", "a"])
            if title_elem:
                listing["title"] = title_elem.get_text(strip=True)
            
            # Extraire le prix
            price_text = element.get_text()
            price_match = re.search(r"(\d+(?:\s?\d{3})*)\s*€", price_text)
            if price_match:
                listing["price"] = int(price_match.group(1).replace(" ", ""))
            
            # Extraire la surface
            surface_match = re.search(r"(\d+(?:[.,]\d+)?)\s*m²", price_text)
            if surface_match:
                listing["surface_area"] = float(surface_match.group(1).replace(",", "."))
            
            # Extraire le nombre de pièces
            rooms_match = re.search(r"(\d+)\s*(?:pièce|room|chambre)", price_text, re.IGNORECASE)
            if rooms_match:
                listing["number_of_rooms"] = int(rooms_match.group(1))
            
            # Extraire le code postal
            postal_match = re.search(r"\b(\d{5})\b", price_text)
            if postal_match:
                listing["postal_code"] = postal_match.group(1)
            
            # Extraire l'URL de l'annonce
            link = element.find("a", href=True)
            if link:
                listing["listing_url"] = urljoin(self.base_url, link["href"])
            
            # Extraire les images
            images = element.find_all("img")
            for img in images:
                src = img.get("src") or img.get("data-src")
                if src:
                    listing["image_urls"].append(urljoin(self.base_url, src))
            
            # Déterminer le type de bien (heuristique)
            title_lower = (listing["title"] or "").lower()
            if "maison" in title_lower or "house" in title_lower:
                listing["property_type"] = "house"
            elif "appartement" in title_lower or "apartment" in title_lower or "appart" in title_lower:
                listing["property_type"] = "apartment"
            elif "terrain" in title_lower or "land" in title_lower:
                listing["property_type"] = "land"
            elif "commercial" in title_lower or "local" in title_lower:
                listing["property_type"] = "commercial"
            else:
                listing["property_type"] = "other"
            
            # Déterminer le type d'opération (heuristique)
            if "location" in title_lower or "rent" in title_lower or "louer" in title_lower:
                listing["operation_type"] = "rental"
            else:
                listing["operation_type"] = "sale"
            
            # Valider que les données essentielles sont présentes
            if listing["title"] and listing["price"] and listing["listing_url"]:
                return listing
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing listing element: {e}")
            return None

    def extract_postal_code_from_url(self, url: str) -> Optional[str]:
        """
        Extraire le code postal depuis l'URL.
        
        Args:
            url: URL
            
        Returns:
            Code postal ou None
        """
        match = re.search(r"/(\d{5})", url)
        if match:
            return match.group(1)
        return None
