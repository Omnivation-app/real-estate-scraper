"""
Module de gestion des contraintes légales et du throttling.

Fonctionnalités :
- Respect du fichier robots.txt
- Throttling configurable (délais entre requêtes)
- Gestion des erreurs réseau (429, 403, captchas)
- Respect du RGPD (pas de collecte de données personnelles)
- Configuration pour activer/désactiver les domaines
"""

import time
import logging
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class LegalCompliance:
    """
    Gestionnaire de conformité légale pour le scraping.
    
    Responsabilités :
    - Vérifier les droits de scraping (robots.txt)
    - Appliquer le throttling
    - Tracker les tentatives échouées
    - Respecter les limites de taux (rate limiting)
    """

    def __init__(self):
        """Initialiser le gestionnaire de conformité."""
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.last_request_time: Dict[str, float] = defaultdict(float)
        self.request_counts: Dict[str, list] = defaultdict(list)  # timestamps des requêtes
        self.blocked_domains: Dict[str, datetime] = {}
        self.throttle_delays: Dict[str, float] = defaultdict(lambda: 2.0)  # délai par défaut
        self.max_requests_per_hour: Dict[str, int] = defaultdict(lambda: 100)

    def set_domain_config(self, domain: str, throttle_delay: float, max_requests_per_hour: int):
        """
        Configurer les paramètres de throttling pour un domaine.
        
        Args:
            domain: Domaine (ex: "seloger.com")
            throttle_delay: Délai minimum entre deux requêtes (secondes)
            max_requests_per_hour: Nombre max de requêtes par heure
        """
        self.throttle_delays[domain] = max(throttle_delay, 0.5)  # Minimum 0.5s
        self.max_requests_per_hour[domain] = max(max_requests_per_hour, 1)
        logger.info(f"Domain config set: {domain} - delay={throttle_delay}s, max={max_requests_per_hour}/h")

    def can_scrape(self, url: str, user_agent: str = "Mozilla/5.0") -> tuple[bool, Optional[str]]:
        """
        Vérifier si le scraping d'une URL est autorisé.
        
        Args:
            url: URL à scraper
            user_agent: User-Agent à utiliser
            
        Returns:
            (autorisé: bool, raison_refus: Optional[str])
        """
        domain = urlparse(url).netloc
        
        # Vérifier si le domaine est bloqué temporairement
        if domain in self.blocked_domains:
            if datetime.now() < self.blocked_domains[domain]:
                return False, f"Domain {domain} is temporarily blocked (rate limited)"
            else:
                del self.blocked_domains[domain]
        
        # Vérifier le rate limiting (max requêtes par heure)
        if not self._check_rate_limit(domain):
            self.blocked_domains[domain] = datetime.now() + timedelta(hours=1)
            return False, f"Rate limit exceeded for {domain} (max {self.max_requests_per_hour[domain]}/hour)"
        
        # Vérifier robots.txt
        if not self._check_robots_txt(domain, url, user_agent):
            return False, f"URL {url} is disallowed by robots.txt"
        
        return True, None

    def wait_before_request(self, domain: str):
        """
        Attendre le délai de throttling avant une requête.
        
        Args:
            domain: Domaine cible
        """
        delay = self.throttle_delays[domain]
        last_time = self.last_request_time[domain]
        elapsed = time.time() - last_time
        
        if elapsed < delay:
            wait_time = delay - elapsed
            logger.debug(f"Throttling {domain}: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()
        self.request_counts[domain].append(time.time())

    def _check_robots_txt(self, domain: str, url: str, user_agent: str) -> bool:
        """
        Vérifier si l'URL est autorisée par robots.txt.
        
        IMPORTANT : Cette fonction respecte les directives robots.txt.
        Avant de scraper un site, vérifier manuellement ses CGU.
        
        Args:
            domain: Domaine
            url: URL complète
            user_agent: User-Agent
            
        Returns:
            True si autorisé, False sinon
        """
        try:
            # Charger robots.txt en cache
            if domain not in self.robots_cache:
                robots_url = f"https://{domain}/robots.txt"
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self.robots_cache[domain] = rp
                except Exception as e:
                    logger.warning(f"Could not read robots.txt for {domain}: {e}")
                    # Si robots.txt n'existe pas, on assume que le scraping est autorisé
                    return True
            
            rp = self.robots_cache[domain]
            is_allowed = rp.can_fetch(user_agent, url)
            
            if not is_allowed:
                logger.warning(f"robots.txt disallows: {url}")
            
            return is_allowed
            
        except Exception as e:
            logger.error(f"Error checking robots.txt for {domain}: {e}")
            return True  # En cas d'erreur, on autorise (fail-safe)

    def _check_rate_limit(self, domain: str) -> bool:
        """
        Vérifier si le rate limit n'est pas dépassé.
        
        Args:
            domain: Domaine
            
        Returns:
            True si on peut faire une requête, False sinon
        """
        now = time.time()
        one_hour_ago = now - 3600
        
        # Nettoyer les anciens timestamps
        self.request_counts[domain] = [
            ts for ts in self.request_counts[domain]
            if ts > one_hour_ago
        ]
        
        max_requests = self.max_requests_per_hour[domain]
        current_count = len(self.request_counts[domain])
        
        if current_count >= max_requests:
            logger.warning(f"Rate limit approaching for {domain}: {current_count}/{max_requests}")
            return False
        
        return True

    def handle_error(self, domain: str, status_code: int, error_msg: str):
        """
        Gérer les erreurs de scraping et adapter la stratégie.
        
        Args:
            domain: Domaine
            status_code: Code HTTP (429, 403, 500, etc.)
            error_msg: Message d'erreur
        """
        if status_code == 429:  # Too Many Requests
            logger.error(f"Rate limited by {domain}: {error_msg}")
            # Augmenter le délai de throttling
            self.throttle_delays[domain] *= 2
            # Bloquer temporairement
            self.blocked_domains[domain] = datetime.now() + timedelta(hours=1)
            
        elif status_code == 403:  # Forbidden
            logger.error(f"Access forbidden for {domain}: {error_msg}")
            # Vérifier si c'est un captcha
            if "captcha" in error_msg.lower():
                logger.warning(f"Captcha detected for {domain}, blocking temporarily")
                self.blocked_domains[domain] = datetime.now() + timedelta(hours=2)
            
        elif status_code == 500:  # Server Error
            logger.warning(f"Server error for {domain}: {error_msg}")
            # Augmenter légèrement le délai
            self.throttle_delays[domain] *= 1.5
        
        elif status_code in [408, 504]:  # Timeout
            logger.warning(f"Timeout for {domain}: {error_msg}")
            self.throttle_delays[domain] *= 1.5


class RGPDCompliance:
    """
    Gestionnaire de conformité RGPD.
    
    Principes :
    - Ne collecter que les données publiques nécessaires
    - Ne pas collecter de données personnelles
    - Respecter les droits des utilisateurs
    """

    @staticmethod
    def is_personal_data(field_name: str, value: str) -> bool:
        """
        Vérifier si une donnée est personnelle (à ne pas collecter).
        
        Args:
            field_name: Nom du champ
            value: Valeur
            
        Returns:
            True si c'est une donnée personnelle
        """
        personal_indicators = [
            "email", "phone", "mobile", "whatsapp",
            "social_media", "facebook", "instagram", "linkedin",
            "name", "firstname", "lastname", "person",
            "address", "home", "apartment", "resident"
        ]
        
        field_lower = field_name.lower()
        return any(indicator in field_lower for indicator in personal_indicators)

    @staticmethod
    def sanitize_data(data: dict) -> dict:
        """
        Nettoyer les données pour respecter le RGPD.
        
        Args:
            data: Données brutes
            
        Returns:
            Données nettoyées (sans données personnelles)
        """
        sanitized = {}
        for key, value in data.items():
            if not RGPDCompliance.is_personal_data(key, str(value)):
                sanitized[key] = value
            else:
                logger.debug(f"Removing personal data: {key}")
        
        return sanitized


# Instances globales
legal_compliance = LegalCompliance()
rgpd_compliance = RGPDCompliance()
