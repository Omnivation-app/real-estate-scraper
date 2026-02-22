"""
Système de mise à jour continue et monitoring du scraping
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from celery import Celery, Task
import schedule
import time

from app.models_decentralized import (
    Agency, AggregatedListing, ScrapingLog, ListingHistory,
    MarketStatistics, generate_listing_hash, calculate_data_quality_score
)
from app.scraper.intelligent_scraper import IntelligentScraper, ListingDeduplicator
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# Celery app
celery_app = Celery('real_estate_scraper')
celery_app.conf.broker_url = 'redis://localhost:6379/0'
celery_app.conf.result_backend = 'redis://localhost:6379/0'


class ContinuousScrapingEngine:
    """Moteur de scraping continu"""
    
    def __init__(self, db: Session, scraper: IntelligentScraper):
        self.db = db
        self.scraper = scraper
        self.deduplicator = ListingDeduplicator()
    
    async def scrape_all_agencies(self):
        """Scrape toutes les agences actives"""
        
        # Récupérer les agences actives
        agencies = self.db.query(Agency).filter(
            Agency.is_active == True
        ).all()
        
        logger.info(f"Scraping {len(agencies)} agences")
        
        # Scraper en parallèle (par batch)
        batch_size = 10
        for i in range(0, len(agencies), batch_size):
            batch = agencies[i:i + batch_size]
            
            tasks = [self.scrape_agency(agency) for agency in batch]
            await asyncio.gather(*tasks)
            
            # Respecter les limites
            await asyncio.sleep(5)
    
    async def scrape_agency(self, agency: Agency):
        """Scrape une agence"""
        
        try:
            logger.info(f"Scraping {agency.name} ({agency.website_url})")
            
            # Marquer comme en cours
            agency.scraping_status = "active"
            agency.last_scraped = datetime.utcnow()
            self.db.commit()
            
            # Récupérer les annonces
            listings = await self.scraper.scrape_agency(agency.website_url)
            
            if not listings:
                logger.warning(f"Aucune annonce trouvée pour {agency.name}")
                agency.scraping_status = "failed"
                agency.scraping_error = "No listings found"
                agency.scraping_error_count += 1
                self.db.commit()
                return
            
            # Traiter les annonces
            new_count, updated_count, removed_count = await self.process_listings(
                agency, listings
            )
            
            # Mettre à jour l'agence
            agency.scraping_status = "success"
            agency.scraping_error = None
            agency.scraping_error_count = 0
            agency.total_listings = len(listings)
            agency.active_listings = len([l for l in listings if l.get('is_active', True)])
            self.db.commit()
            
            # Créer un log
            await self.create_scraping_log(
                agency, "success", len(listings), new_count, updated_count, removed_count
            )
            
            logger.info(f"✓ {agency.name}: {new_count} new, {updated_count} updated, {removed_count} removed")
            
        except Exception as e:
            logger.error(f"✗ Erreur scraping {agency.name}: {e}")
            
            agency.scraping_status = "failed"
            agency.scraping_error = str(e)
            agency.scraping_error_count += 1
            
            # Marquer comme bloquée après 5 erreurs
            if agency.scraping_error_count >= 5:
                agency.scraping_status = "blocked"
                logger.warning(f"Agence {agency.name} bloquée après {agency.scraping_error_count} erreurs")
            
            self.db.commit()
            
            await self.create_scraping_log(
                agency, "failed", 0, 0, 0, 0, str(e)
            )
    
    async def process_listings(self, agency: Agency, listings: List[Dict]) -> tuple:
        """Traite les annonces d'une agence"""
        
        new_count = 0
        updated_count = 0
        removed_count = 0
        
        # Récupérer les annonces précédentes
        previous_listings = self.db.query(AggregatedListing).filter(
            AggregatedListing.agency_id == agency.id,
            AggregatedListing.is_active == True
        ).all()
        
        previous_urls = {l.source_url for l in previous_listings}
        current_urls = set()
        
        # Traiter chaque annonce
        for listing_data in listings:
            try:
                # Générer le hash
                hash_value = generate_listing_hash(
                    listing_data.get('title', ''),
                    listing_data.get('price', ''),
                    listing_data.get('address', '')
                )
                
                # Vérifier si elle existe
                existing = self.db.query(AggregatedListing).filter(
                    AggregatedListing.hash == hash_value
                ).first()
                
                if existing:
                    # Mise à jour
                    await self.update_listing(existing, listing_data)
                    updated_count += 1
                else:
                    # Nouvelle annonce
                    await self.create_listing(agency, listing_data, hash_value)
                    new_count += 1
                
                current_urls.add(listing_data.get('source_url', ''))
                
            except Exception as e:
                logger.error(f"Erreur traitement annonce: {e}")
                continue
        
        # Marquer les annonces supprimées
        removed_urls = previous_urls - current_urls
        for url in removed_urls:
            listing = self.db.query(AggregatedListing).filter(
                AggregatedListing.source_url == url
            ).first()
            
            if listing:
                listing.is_active = False
                
                # Créer un log d'historique
                history = ListingHistory(
                    listing_id=listing.id,
                    change_type="removed",
                    previous_data={"is_active": True},
                    new_data={"is_active": False}
                )
                self.db.add(history)
                removed_count += 1
        
        self.db.commit()
        
        return new_count, updated_count, removed_count
    
    async def create_listing(self, agency: Agency, listing_data: Dict, hash_value: str):
        """Crée une nouvelle annonce"""
        
        # Calculer le score de qualité
        quality_score = calculate_data_quality_score(
            type('obj', (object,), listing_data)()
        )
        
        listing = AggregatedListing(
            hash=hash_value,
            title=listing_data.get('title', ''),
            description=listing_data.get('description'),
            price=int(listing_data.get('price', 0)) if listing_data.get('price') else None,
            property_type=listing_data.get('property_type'),
            rooms=int(listing_data.get('rooms', 0)) if listing_data.get('rooms') else None,
            surface=int(listing_data.get('surface', 0)) if listing_data.get('surface') else None,
            address=listing_data.get('address'),
            postal_code=listing_data.get('postal_code'),
            city=listing_data.get('city'),
            latitude=listing_data.get('latitude'),
            longitude=listing_data.get('longitude'),
            agency_id=agency.id,
            source_url=listing_data.get('source_url', ''),
            photos=listing_data.get('photos', []),
            features=listing_data.get('features', {}),
            data_quality_score=quality_score
        )
        
        self.db.add(listing)
        self.db.flush()
        
        # Créer un log d'historique
        history = ListingHistory(
            listing_id=listing.id,
            change_type="created",
            new_data=listing_data
        )
        self.db.add(history)
        
        # Notifier les utilisateurs intéressés
        await self.notify_new_listing(listing)
    
    async def update_listing(self, listing: AggregatedListing, listing_data: Dict):
        """Met à jour une annonce"""
        
        # Sauvegarder les données précédentes
        previous_data = {
            'title': listing.title,
            'price': listing.price,
            'description': listing.description
        }
        
        # Mettre à jour
        listing.title = listing_data.get('title', listing.title)
        listing.description = listing_data.get('description', listing.description)
        listing.price = int(listing_data.get('price', listing.price)) if listing_data.get('price') else listing.price
        listing.photos = listing_data.get('photos', listing.photos)
        listing.updated_at = datetime.utcnow()
        
        self.db.flush()
        
        # Créer un log d'historique si changement important
        if previous_data['price'] != listing.price:
            history = ListingHistory(
                listing_id=listing.id,
                change_type="updated",
                previous_data=previous_data,
                new_data={
                    'title': listing.title,
                    'price': listing.price,
                    'description': listing.description
                }
            )
            self.db.add(history)
    
    async def create_scraping_log(
        self, agency: Agency, status: str, listings_found: int,
        new: int, updated: int, removed: int, error: str = None
    ):
        """Crée un log de scraping"""
        
        log = ScrapingLog(
            agency_id=agency.id,
            status=status,
            listings_found=listings_found,
            listings_new=new,
            listings_updated=updated,
            listings_removed=removed,
            error_message=error,
            end_time=datetime.utcnow()
        )
        
        self.db.add(log)
        self.db.commit()
    
    async def notify_new_listing(self, listing: AggregatedListing):
        """Notifie les utilisateurs d'une nouvelle annonce"""
        
        # Récupérer les alertes correspondantes
        from app.models_decentralized import SearchAlert
        
        alerts = self.db.query(SearchAlert).filter(
            SearchAlert.is_active == True,
            SearchAlert.postal_code == listing.postal_code
        ).all()
        
        for alert in alerts:
            # Vérifier les critères
            if self._matches_alert(listing, alert):
                # Envoyer notification
                await self._send_notification(alert, listing)
    
    @staticmethod
    def _matches_alert(listing: AggregatedListing, alert) -> bool:
        """Vérifie si l'annonce correspond à l'alerte"""
        
        # Vérifier le prix
        if alert.price_min and listing.price < alert.price_min:
            return False
        if alert.price_max and listing.price > alert.price_max:
            return False
        
        # Vérifier la surface
        if alert.surface_min and listing.surface < alert.surface_min:
            return False
        if alert.surface_max and listing.surface > alert.surface_max:
            return False
        
        # Vérifier le type de bien
        if alert.property_type and listing.property_type != alert.property_type:
            return False
        
        # Vérifier les pièces
        if alert.rooms_min and listing.rooms < alert.rooms_min:
            return False
        if alert.rooms_max and listing.rooms > alert.rooms_max:
            return False
        
        return True
    
    async def _send_notification(self, alert, listing: AggregatedListing):
        """Envoie une notification"""
        
        from app.notifications import notification_service
        
        try:
            if alert.notify_by_email:
                await notification_service.send_new_listing_email(alert.user_id, listing)
            
            if alert.notify_by_sms:
                await notification_service.send_new_listing_sms(alert.user_id, listing)
            
            # Mettre à jour last_notified
            alert.last_notified = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Erreur notification: {e}")


class ScrapingScheduler:
    """Planificateur de scraping"""
    
    def __init__(self, db: Session, scraper: IntelligentScraper):
        self.engine = ContinuousScrapingEngine(db, scraper)
        self.db = db
    
    def schedule_scraping(self):
        """Planifie le scraping"""
        
        # Scraper toutes les agences chaque jour à 2h du matin
        schedule.every().day.at("02:00").do(self._run_full_scraping)
        
        # Scraper les agences prioritaires toutes les 6 heures
        schedule.every(6).hours.do(self._run_priority_scraping)
        
        # Mettre à jour les statistiques du marché toutes les heures
        schedule.every().hour.do(self._update_market_statistics)
        
        # Nettoyer les doublons tous les jours
        schedule.every().day.at("03:00").do(self._cleanup_duplicates)
        
        # Lancer le scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    async def _run_full_scraping(self):
        """Lance le scraping complet"""
        logger.info("Démarrage du scraping complet")
        await self.engine.scrape_all_agencies()
        logger.info("Scraping complet terminé")
    
    async def _run_priority_scraping(self):
        """Lance le scraping des agences prioritaires"""
        
        # Agences qui n'ont pas été scrapées depuis plus de 24h
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        agencies = self.db.query(Agency).filter(
            Agency.is_active == True,
            Agency.last_scraped < cutoff_time
        ).all()
        
        logger.info(f"Scraping {len(agencies)} agences prioritaires")
        
        for agency in agencies:
            await self.engine.scrape_agency(agency)
    
    async def _update_market_statistics(self):
        """Met à jour les statistiques du marché"""
        
        logger.info("Mise à jour des statistiques du marché")
        
        # Récupérer les codes postaux uniques
        postal_codes = self.db.query(AggregatedListing.postal_code).distinct().all()
        
        for (postal_code,) in postal_codes:
            if not postal_code:
                continue
            
            # Calculer les statistiques
            listings = self.db.query(AggregatedListing).filter(
                AggregatedListing.postal_code == postal_code,
                AggregatedListing.is_active == True
            ).all()
            
            if not listings:
                continue
            
            # Récupérer ou créer les statistiques
            stats = self.db.query(MarketStatistics).filter(
                MarketStatistics.postal_code == postal_code
            ).first()
            
            if not stats:
                stats = MarketStatistics(postal_code=postal_code, city=listings[0].city)
                self.db.add(stats)
            
            # Mettre à jour
            prices = [l.price for l in listings if l.price]
            
            stats.total_listings = len(listings)
            stats.active_listings = len([l for l in listings if l.is_active])
            stats.average_price = int(sum(prices) / len(prices)) if prices else None
            stats.median_price = sorted(prices)[len(prices) // 2] if prices else None
            stats.price_min = min(prices) if prices else None
            stats.price_max = max(prices) if prices else None
            
            stats.apartments_count = len([l for l in listings if l.property_type == 'apartment'])
            stats.houses_count = len([l for l in listings if l.property_type == 'house'])
            stats.studios_count = len([l for l in listings if l.property_type == 'studio'])
            
            stats.updated_at = datetime.utcnow()
            
            self.db.commit()
    
    async def _cleanup_duplicates(self):
        """Nettoie les doublons"""
        
        logger.info("Nettoyage des doublons")
        
        # Récupérer les annonces avec le même hash
        duplicates = self.db.query(AggregatedListing).filter(
            AggregatedListing.is_duplicate == False
        ).all()
        
        seen_hashes = {}
        
        for listing in duplicates:
            if listing.hash in seen_hashes:
                # C'est un doublon
                listing.is_duplicate = True
                listing.duplicate_of = seen_hashes[listing.hash]
            else:
                seen_hashes[listing.hash] = listing.id
        
        self.db.commit()
        logger.info(f"Nettoyage terminé")


# Celery tasks

@celery_app.task
def scrape_agency_task(agency_id: int):
    """Task Celery pour scraper une agence"""
    
    db = SessionLocal()
    scraper = IntelligentScraper()
    engine = ContinuousScrapingEngine(db, scraper)
    
    try:
        agency = db.query(Agency).filter(Agency.id == agency_id).first()
        if agency:
            asyncio.run(engine.scrape_agency(agency))
    finally:
        db.close()


@celery_app.task
def update_market_statistics_task():
    """Task Celery pour mettre à jour les statistiques"""
    
    db = SessionLocal()
    scraper = IntelligentScraper()
    scheduler = ScrapingScheduler(db, scraper)
    
    try:
        asyncio.run(scheduler._update_market_statistics())
    finally:
        db.close()


@celery_app.task
def cleanup_duplicates_task():
    """Task Celery pour nettoyer les doublons"""
    
    db = SessionLocal()
    scraper = IntelligentScraper()
    scheduler = ScrapingScheduler(db, scraper)
    
    try:
        asyncio.run(scheduler._cleanup_duplicates())
    finally:
        db.close()
