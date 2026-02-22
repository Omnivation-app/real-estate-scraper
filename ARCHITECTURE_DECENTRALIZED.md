# Architecture de Scraping Décentralisé — Toutes les Agences Immobilières

Architecture complète pour découvrir et scraper **TOUTES les agences immobilières** sans exception.

## 1. Vue d'ensemble Générale

```
┌─────────────────────────────────────────────────────────────┐
│                    DÉCOUVERTE DES AGENCES                    │
├─────────────────────────────────────────────────────────────┤
│  Google Maps API  │  Pages Jaunes  │  Annuaire  │  Scraping │
│  (Géolocalisation)│  (Listings)    │  (Données) │  (Web)    │
└────────────┬──────────────────────────────────────────┬─────┘
             │                                          │
             ▼                                          ▼
    ┌─────────────────────────────────────────────────────────┐
    │         BASE DE DONNÉES DES AGENCES                     │
    │  ┌──────────────────────────────────────────────────┐   │
    │  │ ID | Nom | URL | Adresse | Tel | Email | SIREN  │   │
    │  │ 1  | Agence A | url.fr | ... | ... | ... | ...  │   │
    │  │ 2  | Agence B | url.fr | ... | ... | ... | ...  │   │
    │  │ ... | ... | ... | ... | ... | ... | ...         │   │
    │  └──────────────────────────────────────────────────┘   │
    └────────────┬──────────────────────────────────────┬─────┘
                 │                                      │
                 ▼                                      ▼
    ┌──────────────────────┐         ┌──────────────────────────┐
    │  SCRAPER INTELLIGENT │         │  DÉTECTEUR DE FORMAT     │
    │  (Multi-domaines)    │         │  (Analyse HTML/CSS)      │
    │                      │         │                          │
    │  - Selenium/Puppeteer│         │  - Détecte structure     │
    │  - Gestion JS        │         │  - Identifie patterns    │
    │  - Proxy rotation    │         │  - Génère parsers        │
    │  - Retry logic       │         │                          │
    └──────────────────────┘         └──────────────────────────┘
             │                                      │
             └──────────────────┬───────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  ANNONCES AGRÉGÉES            │
                │  (Base de données centralisée)│
                │                               │
                │  - Titre, Prix, Surface      │
                │  - Localisation, Photos      │
                │  - Agence source             │
                │  - Date de scraping          │
                └───────────────────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  API & INTERFACE WEB          │
                │                               │
                │  - Recherche unifiée          │
                │  - Filtres avancés            │
                │  - Alertes                    │
                │  - Cartes interactives        │
                └───────────────────────────────┘
```

## 2. Phase 1 : Découverte des Agences

### 2.1 Sources de Découverte

```
┌─────────────────────────────────────────────────────────┐
│              SOURCES DE DÉCOUVERTE                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. GOOGLE MAPS API                                    │
│     - Recherche "agence immobilière" par code postal   │
│     - Récupère : nom, adresse, téléphone, site web    │
│     - Couverture : 100% des agences géolocalisées     │
│                                                         │
│  2. PAGES JAUNES (pagesjaunes.fr)                      │
│     - Scraper la catégorie "Agences immobilières"      │
│     - Récupère : nom, adresse, téléphone, email       │
│     - Couverture : ~95% des agences                    │
│                                                         │
│  3. ANNUAIRE PROFESSIONNEL (kompass.com)               │
│     - Recherche par secteur d'activité                 │
│     - Récupère : SIREN, SIRET, dirigeants             │
│     - Couverture : Données légales                     │
│                                                         │
│  4. SCRAPING WEB GÉNÉRAL                               │
│     - Recherche Google : "agence immobilière [ville]"  │
│     - Récupère : URLs des sites web                    │
│     - Couverture : Agences sans Google Maps            │
│                                                         │
│  5. LINKEDIN (API officielle)                          │
│     - Recherche entreprises "immobilier"               │
│     - Récupère : Site web, description, localisation  │
│     - Couverture : Agences modernes                    │
│                                                         │
│  6. ANNUAIRES RÉGIONAUX                                │
│     - Chambres d'agriculture, CCI locales              │
│     - Récupère : Listes exhaustives par région         │
│     - Couverture : Petites agences locales             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Modèle de Données des Agences

```python
class Agency(Base):
    __tablename__ = "agencies"
    
    id = Column(Integer, primary_key=True)
    
    # Identité
    name = Column(String(255), unique=True, index=True)
    siren = Column(String(9), unique=True, nullable=True)
    siret = Column(String(14), unique=True, nullable=True)
    
    # Contact
    address = Column(String(500))
    postal_code = Column(String(5), index=True)
    city = Column(String(100), index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Web
    website_url = Column(String(500), unique=True, index=True)
    website_type = Column(String(50))  # "custom", "wordpress", "wix", etc.
    
    # Géolocalisation
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Sources de découverte
    discovered_from = Column(JSON)  # ["google_maps", "pages_jaunes", ...]
    
    # Scraping
    last_scraped = Column(DateTime, nullable=True)
    scraping_status = Column(String(50))  # "pending", "active", "failed", "blocked"
    scraping_error = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

## 3. Phase 2 : Scraper Intelligent Multi-Domaines

### 3.1 Architecture du Scraper

```python
class IntelligentScraper:
    """
    Scraper capable de s'adapter à n'importe quel site d'agence
    """
    
    def __init__(self):
        self.browser = None  # Selenium/Puppeteer
        self.detector = FormatDetector()
        self.parser = DynamicParser()
        self.proxy_manager = ProxyRotation()
    
    async def scrape_agency(self, agency: Agency):
        """Scraper une agence"""
        try:
            # 1. Accéder au site
            html = await self.fetch_page(agency.website_url)
            
            # 2. Détecter le format
            format_info = self.detector.detect(html, agency.website_url)
            
            # 3. Parser les annonces
            listings = self.parser.parse(html, format_info)
            
            # 4. Sauvegarder
            await self.save_listings(listings, agency)
            
        except Exception as e:
            await self.handle_error(agency, e)
```

### 3.2 Détecteur de Format Automatique

```python
class FormatDetector:
    """
    Détecte automatiquement le format des annonces
    """
    
    PATTERNS = {
        "wordpress": {
            "selectors": [".post", ".property", ".listing"],
            "indicators": ["wp-content", "wp-includes"]
        },
        "wix": {
            "selectors": ["[data-mesh-id]", ".wixui"],
            "indicators": ["wix.com", "wixstatic.com"]
        },
        "shopify": {
            "selectors": [".product", ".listing"],
            "indicators": ["shopify.com", "cdn.shopify.com"]
        },
        "custom": {
            "selectors": ["[data-listing]", ".property-card", ".annonce"],
            "indicators": []
        },
        "immobilier_pro": {
            "selectors": [".bien", ".annonce", ".property"],
            "indicators": ["immobilier", "bien", "annonce"]
        }
    }
    
    def detect(self, html: str, url: str) -> dict:
        """Détecte le type de site et les sélecteurs"""
        
        # 1. Vérifier les indicateurs
        for platform, patterns in self.PATTERNS.items():
            if self.check_indicators(html, url, patterns["indicators"]):
                return {
                    "platform": platform,
                    "selectors": patterns["selectors"]
                }
        
        # 2. Analyser la structure HTML
        structure = self.analyze_structure(html)
        
        # 3. Générer les sélecteurs dynamiquement
        selectors = self.generate_selectors(structure)
        
        return {
            "platform": "custom",
            "selectors": selectors,
            "structure": structure
        }
    
    def generate_selectors(self, structure: dict) -> list:
        """Génère les sélecteurs CSS/XPath"""
        selectors = []
        
        # Chercher les patterns courants
        keywords = ["annonce", "bien", "property", "listing", "offer"]
        
        for keyword in keywords:
            # Classes
            selectors.append(f".{keyword}")
            selectors.append(f"[class*='{keyword}']")
            
            # IDs
            selectors.append(f"#{keyword}")
            selectors.append(f"[id*='{keyword}']")
            
            # Data attributes
            selectors.append(f"[data-{keyword}]")
        
        return selectors
```

### 3.3 Parser Dynamique

```python
class DynamicParser:
    """
    Parse les annonces selon le format détecté
    """
    
    FIELD_PATTERNS = {
        "title": ["h1", "h2", ".title", ".name", "[data-title]"],
        "price": [".price", ".montant", "[data-price]", "span:contains('€')"],
        "surface": [".surface", ".m2", "[data-surface]"],
        "rooms": [".rooms", ".pieces", "[data-rooms]"],
        "description": [".description", ".details", "p"],
        "images": ["img", "[data-image]", ".gallery"],
        "contact": [".contact", ".agent", "[data-agent]"]
    }
    
    def parse(self, html: str, format_info: dict) -> list:
        """Parse les annonces"""
        listings = []
        
        # Récupérer les éléments annonces
        soup = BeautifulSoup(html, 'html.parser')
        listing_elements = soup.select(", ".join(format_info["selectors"]))
        
        for element in listing_elements:
            listing = self.extract_listing(element)
            if listing:
                listings.append(listing)
        
        return listings
    
    def extract_listing(self, element) -> dict:
        """Extrait les données d'une annonce"""
        listing = {}
        
        for field, patterns in self.FIELD_PATTERNS.items():
            for pattern in patterns:
                try:
                    value = element.select_one(pattern)
                    if value:
                        listing[field] = value.get_text(strip=True)
                        break
                except:
                    continue
        
        return listing if listing else None
```

## 4. Phase 3 : Gestion des Défis Techniques

### 4.1 Gestion des Sites JavaScript

```python
class JavaScriptHandler:
    """Gère les sites avec contenu chargé en JavaScript"""
    
    async def scrape_js_site(self, url: str):
        """Scrape un site avec contenu JS"""
        
        # Utiliser Puppeteer pour les sites JS
        browser = await launch()
        page = await browser.newPage()
        
        # Attendre le chargement
        await page.goto(url, waitUntil='networkidle2')
        
        # Attendre les annonces
        await page.waitForSelector('.listing, [data-listing]', timeout=5000)
        
        # Récupérer le contenu
        html = await page.content()
        
        await browser.close()
        
        return html
```

### 4.2 Rotation de Proxies

```python
class ProxyRotation:
    """Gère la rotation des proxies pour éviter les blocages"""
    
    def __init__(self):
        self.proxies = [
            "http://proxy1.com:8080",
            "http://proxy2.com:8080",
            "http://proxy3.com:8080",
        ]
        self.current_index = 0
    
    def get_proxy(self):
        """Récupère le prochain proxy"""
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
```

### 4.3 Gestion des Erreurs et Retry

```python
class ErrorHandler:
    """Gère les erreurs et les retries"""
    
    async def retry_with_backoff(self, func, max_retries=3):
        """Retry avec backoff exponentiel"""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                # Backoff exponentiel
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{max_retries} après {wait_time}s")
                await asyncio.sleep(wait_time)
```

## 5. Phase 4 : Base de Données Agrégée

### 5.1 Modèle d'Annonces Agrégées

```python
class AggregatedListing(Base):
    __tablename__ = "aggregated_listings"
    
    id = Column(Integer, primary_key=True)
    
    # Données de base
    title = Column(String(500))
    description = Column(Text)
    price = Column(Integer, nullable=True)
    price_per_sqm = Column(Integer, nullable=True)
    
    # Caractéristiques
    property_type = Column(String(50))
    rooms = Column(Integer, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    surface = Column(Integer, nullable=True)
    
    # Localisation
    address = Column(String(500))
    postal_code = Column(String(5), index=True)
    city = Column(String(100), index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Agence source
    agency_id = Column(Integer, ForeignKey("agencies.id"))
    agency = relationship("Agency")
    
    # Métadonnées
    source_url = Column(String(1000), unique=True)
    photos = Column(JSON)
    
    # Scraping
    scraped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Déduplication
    hash = Column(String(64), unique=True, index=True)  # SHA256 du contenu
```

### 5.2 Déduplication des Annonces

```python
class DeduplicationEngine:
    """Évite les doublons entre agences"""
    
    def generate_hash(self, listing: dict) -> str:
        """Génère un hash unique pour une annonce"""
        
        # Créer une signature basée sur les données clés
        signature = f"{listing['title']}|{listing['price']}|{listing['address']}"
        
        # Normaliser
        signature = signature.lower().strip()
        
        # Hash SHA256
        return hashlib.sha256(signature.encode()).hexdigest()
    
    async def check_duplicate(self, listing: dict) -> bool:
        """Vérifie si l'annonce existe déjà"""
        
        hash_value = self.generate_hash(listing)
        
        existing = db.query(AggregatedListing).filter(
            AggregatedListing.hash == hash_value
        ).first()
        
        return existing is not None
```

## 6. Phase 5 : Mise à Jour Continue

### 6.1 Scheduler de Scraping

```python
class ScrapingScheduler:
    """Planifie le scraping continu de toutes les agences"""
    
    async def schedule_scraping(self):
        """Planifie le scraping"""
        
        # Scraper toutes les agences
        agencies = db.query(Agency).filter(Agency.is_active == True).all()
        
        for agency in agencies:
            # Planifier le scraping
            await self.queue_scraping_job(agency)
    
    async def queue_scraping_job(self, agency: Agency):
        """Ajoute une agence à la queue de scraping"""
        
        # Celery task
        scrape_agency_task.delay(agency.id)
```

### 6.2 Détection des Changements

```python
class ChangeDetector:
    """Détecte les changements d'annonces"""
    
    async def detect_changes(self, agency: Agency):
        """Détecte les nouvelles/supprimées annonces"""
        
        # Récupérer les annonces actuelles
        current_listings = await self.scraper.scrape_agency(agency)
        
        # Récupérer les annonces précédentes
        previous_listings = db.query(AggregatedListing).filter(
            AggregatedListing.agency_id == agency.id,
            AggregatedListing.is_active == True
        ).all()
        
        # Comparer
        new_listings = self.find_new(current_listings, previous_listings)
        removed_listings = self.find_removed(current_listings, previous_listings)
        
        # Notifier
        await self.notify_changes(agency, new_listings, removed_listings)
```

## 7. Flux de Données Complet

```
┌─────────────────────────────────────────────────────────────┐
│  1. DÉCOUVERTE (Quotidienne)                                │
│  ├─ Google Maps API → Trouver nouvelles agences            │
│  ├─ Pages Jaunes → Mettre à jour liste                     │
│  └─ Scraping web → Découvrir agences manquantes            │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  2. SCRAPING (Continu)                                      │
│  ├─ Queue de scraping (Celery)                             │
│  ├─ Scraper intelligent (Selenium/Puppeteer)               │
│  ├─ Détecteur de format (Auto-adapt)                       │
│  └─ Parser dynamique (Extraction)                          │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  3. TRAITEMENT (Temps réel)                                 │
│  ├─ Déduplication (Hash SHA256)                            │
│  ├─ Normalisation (Données)                                │
│  ├─ Géolocalisation (Coordonnées GPS)                      │
│  └─ Validation (Qualité)                                   │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  4. STOCKAGE (Base de données)                              │
│  ├─ Annonces agrégées                                      │
│  ├─ Métadonnées agences                                    │
│  ├─ Historique scraping                                    │
│  └─ Logs d'erreurs                                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  5. RECHERCHE & API (Utilisateurs)                          │
│  ├─ Recherche unifiée (Tous les résultats)                 │
│  ├─ Filtres avancés (Prix, surface, etc.)                  │
│  ├─ Alertes (Nouvelles annonces)                           │
│  └─ Cartes (Géolocalisation)                               │
└─────────────────────────────────────────────────────────────┘
```

## 8. Statistiques Attendues

```
Après 1 mois de scraping :
- Agences découvertes : ~15,000 - 20,000
- Annonces agrégées : ~500,000 - 1,000,000
- Couverture géographique : 100% France
- Mise à jour : Quotidienne

Après 3 mois :
- Agences : ~25,000 - 30,000
- Annonces : ~2,000,000 - 3,000,000
- Historique : Tendances du marché
```

## 9. Défis et Solutions

| Défi | Solution |
|------|----------|
| Blocages IP | Rotation de proxies, VPN |
| Sites JavaScript | Puppeteer, Selenium |
| Structures différentes | Détecteur de format auto |
| Doublons | Hash SHA256 + déduplication |
| Rate limiting | Throttling intelligent |
| Captchas | Service anti-captcha |
| Données incomplètes | Validation + enrichissement |

## 10. Prochaines Étapes

1. ✅ Concevoir l'architecture
2. → Implémenter la découverte des agences
3. → Développer le scraper intelligent
4. → Créer la base de données agrégée
5. → Mettre en place la mise à jour continue
6. → Tester et valider
