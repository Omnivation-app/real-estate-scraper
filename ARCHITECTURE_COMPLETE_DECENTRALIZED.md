# Architecture Complète du Scraper Décentralisé

## 🎯 Vue d'Ensemble

L'application scrape **TOUTES les agences immobilières** sur Internet (pas juste les gros sites) en :

1. **Découvrant automatiquement** les agences via plusieurs sources
2. **Scrapant individuellement** chaque site d'agence
3. **Détectant automatiquement** le format de chaque site
4. **Agrégéant les données** dans une base de données centralisée
5. **Mettant à jour continuellement** les annonces
6. **Notifiant les utilisateurs** des nouvelles annonces

---

## 📊 Architecture Système

```
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEURS (Web/Mobile)                │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              API REST FastAPI (Port 8000)                    │
├─────────────────────────────────────────────────────────────┤
│ • Recherche d'annonces                                      │
│ • Gestion des favoris                                       │
│ • Gestion des alertes                                       │
│ • Authentification JWT                                      │
│ • Statistiques du marché                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Discovery  │ │   Scraper    │ │  Continuous  │
│   Engine     │ │   Engine     │ │  Scheduler   │
└──────────────┘ └──────────────┘ └──────────────┘
        │                │                │
        │                │                │
        ├─────────┬──────┴────────┬───────┤
        │         │               │       │
        ▼         ▼               ▼       ▼
    ┌─────────────────────────────────────────┐
    │     PostgreSQL Database (Port 5432)     │
    ├─────────────────────────────────────────┤
    │ • Agencies (39 colonnes)                │
    │ • Aggregated Listings (25 colonnes)     │
    │ • Scraping Logs                         │
    │ • Listing History                       │
    │ • Market Statistics                     │
    │ • Users & Favorites                     │
    │ • Search Alerts                         │
    └─────────────────────────────────────────┘
        │
        ├─────────────────────────────────────┐
        │                                     │
        ▼                                     ▼
    ┌──────────────┐                ┌──────────────┐
    │ Redis Cache  │                │ Elasticsearch│
    │ (Port 6379)  │                │ (Port 9200)  │
    └──────────────┘                └──────────────┘
```

---

## 🔍 Module de Découverte (Agency Discovery)

### Sources de Découverte

| Source | Méthode | Couverture | Fiabilité |
|--------|---------|-----------|-----------|
| **Google Maps API** | API + Geocoding | Nationale | ⭐⭐⭐⭐⭐ |
| **Pages Jaunes** | Web Scraping | Nationale | ⭐⭐⭐⭐ |
| **Google Search** | Scraping + SerpAPI | Nationale | ⭐⭐⭐⭐ |
| **LinkedIn** | API + Scraping | Entreprises | ⭐⭐⭐ |
| **Annuaires** | Kompass, Societe.com | Nationale | ⭐⭐⭐⭐ |

### Processus de Découverte

```python
# 1. Initialiser le moteur
engine = AgencyDiscoveryEngine(google_maps_api_key)

# 2. Découvrir les agences pour un code postal
agencies = await engine.discover_all_agencies("75015", "Paris")

# 3. Résultat
[
    {
        "name": "Agence XYZ",
        "website_url": "https://agence-xyz.fr",
        "phone": "+33123456789",
        "address": "123 Rue de la Paix, 75015 Paris",
        "discovered_from": ["google_maps", "pages_jaunes"],
        "latitude": 48.8566,
        "longitude": 2.3522
    },
    ...
]
```

### Déduplication

Les agences découvertes sont dédupliquées par URL pour éviter les doublons.

---

## 🤖 Module de Scraping Intelligent

### Détection de Format

Le scraper détecte automatiquement le type de site :

```
┌─────────────────────────────────────────┐
│        Analyse du HTML/URL              │
└─────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│WordPress│ │  Wix  │ │Shopify │
└────────┘ └────────┘ └────────┘
    │         │         │
    └─────────┼─────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Sélecteurs CSS     │
    │  Spécifiques        │
    └─────────────────────┘
```

### Extraction de Données

Pour chaque annonce, le scraper extrait :

| Champ | Type | Exemple |
|-------|------|---------|
| **title** | String | "Bel appartement 3 pièces à Paris" |
| **price** | Integer | 450000 |
| **surface** | Integer | 75 |
| **rooms** | Integer | 3 |
| **bedrooms** | Integer | 2 |
| **bathrooms** | Integer | 1 |
| **address** | String | "123 Rue de la Paix, 75015 Paris" |
| **postal_code** | String | "75015" |
| **city** | String | "Paris" |
| **property_type** | String | "apartment" |
| **description** | Text | "Bel appartement avec vue sur la Tour Eiffel..." |
| **photos** | Array | ["url1", "url2", ...] |
| **features** | JSON | {"parking": true, "balcony": true} |

### Processus de Scraping

```python
# 1. Initialiser le scraper
scraper = IntelligentScraper(proxies=["proxy1", "proxy2"])

# 2. Scraper une agence
listings = await scraper.scrape_agency("https://agence-xyz.fr")

# 3. Résultat
[
    {
        "title": "Appartement 3 pièces",
        "price": 450000,
        "surface": 75,
        "rooms": 3,
        "address": "123 Rue de la Paix, 75015 Paris",
        "postal_code": "75015",
        "city": "Paris",
        "property_type": "apartment",
        "description": "...",
        "photos": ["url1", "url2"],
        "source_url": "https://agence-xyz.fr/annonce/123"
    },
    ...
]
```

### Gestion des Proxies

Le scraper utilise une rotation de proxies pour éviter les blocages IP :

```python
proxy_manager = ProxyRotation([
    "http://proxy1.com:8080",
    "http://proxy2.com:8080",
    "http://proxy3.com:8080"
])

# Chaque requête utilise un proxy différent
proxy = proxy_manager.get_proxy()
```

---

## 💾 Modèles de Base de Données

### Agencies (Agences)

```sql
CREATE TABLE agencies (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    siren VARCHAR(9) UNIQUE,
    siret VARCHAR(14) UNIQUE,
    website_url VARCHAR(1000) UNIQUE NOT NULL,
    website_type VARCHAR(50),
    address VARCHAR(500),
    postal_code VARCHAR(5),
    city VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    discovered_from JSON,
    last_scraped DATETIME,
    scraping_status VARCHAR(50),
    scraping_error TEXT,
    scraping_error_count INTEGER,
    total_listings INTEGER,
    active_listings INTEGER,
    created_at DATETIME,
    updated_at DATETIME,
    is_active BOOLEAN,
    
    INDEX idx_postal_city (postal_code, city),
    INDEX idx_status_updated (scraping_status, updated_at)
);
```

### Aggregated Listings (Annonces Agrégées)

```sql
CREATE TABLE aggregated_listings (
    id INTEGER PRIMARY KEY,
    hash VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    price INTEGER,
    price_per_sqm INTEGER,
    property_type VARCHAR(50),
    rooms INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,
    surface INTEGER,
    address VARCHAR(500),
    postal_code VARCHAR(5),
    city VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT,
    agency_id INTEGER NOT NULL,
    source_url VARCHAR(1000) UNIQUE NOT NULL,
    photos JSON,
    features JSON,
    scraped_at DATETIME,
    updated_at DATETIME,
    is_active BOOLEAN,
    data_quality_score FLOAT,
    is_duplicate BOOLEAN,
    duplicate_of INTEGER,
    view_count INTEGER,
    favorite_count INTEGER,
    
    FOREIGN KEY (agency_id) REFERENCES agencies(id),
    INDEX idx_postal_price (postal_code, price),
    INDEX idx_city_type (city, property_type),
    INDEX idx_agency_active (agency_id, is_active),
    INDEX idx_scraped_active (scraped_at, is_active)
);
```

### Scraping Logs

```sql
CREATE TABLE scraping_logs (
    id INTEGER PRIMARY KEY,
    agency_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    listings_found INTEGER,
    listings_new INTEGER,
    listings_updated INTEGER,
    listings_removed INTEGER,
    error_message TEXT,
    error_type VARCHAR(100),
    start_time DATETIME,
    end_time DATETIME,
    duration_seconds FLOAT,
    created_at DATETIME,
    
    FOREIGN KEY (agency_id) REFERENCES agencies(id),
    INDEX idx_agency_created (agency_id, created_at),
    INDEX idx_status_created (status, created_at)
);
```

---

## ⏰ Système de Mise à Jour Continue

### Planification

| Tâche | Fréquence | Heure |
|-------|-----------|-------|
| Scraping complet | Quotidien | 02:00 |
| Scraping prioritaire | Toutes les 6h | - |
| Mise à jour stats | Toutes les heures | - |
| Nettoyage doublons | Quotidien | 03:00 |

### Processus de Scraping

```
1. Récupérer les agences actives
   ↓
2. Scraper en parallèle (batch de 10)
   ↓
3. Détecter le format du site
   ↓
4. Extraire les annonces
   ↓
5. Dédupliquer
   ↓
6. Comparer avec les annonces précédentes
   ├─ Nouvelles → Créer + Notifier
   ├─ Mises à jour → Mettre à jour + Notifier si changement prix
   └─ Supprimées → Marquer comme inactives
   ↓
7. Créer des logs
   ↓
8. Mettre à jour les statistiques
```

### Notification des Utilisateurs

Quand une nouvelle annonce correspond à une alerte :

```
1. Vérifier les critères de l'alerte
   ├─ Prix (min/max)
   ├─ Surface (min/max)
   ├─ Type de bien
   ├─ Nombre de pièces
   └─ Code postal
   ↓
2. Si match → Envoyer notification
   ├─ Email (si activé)
   └─ SMS (si activé)
   ↓
3. Mettre à jour last_notified
```

---

## 📊 Statistiques du Marché

Calculées automatiquement chaque heure :

```json
{
    "postal_code": "75015",
    "city": "Paris",
    "total_listings": 1250,
    "active_listings": 1180,
    "average_price": 450000,
    "average_price_per_sqm": 6000,
    "median_price": 420000,
    "price_min": 200000,
    "price_max": 1500000,
    "apartments_count": 800,
    "houses_count": 250,
    "studios_count": 130,
    "listings_added_today": 45,
    "listings_added_week": 280,
    "listings_added_month": 1100
}
```

---

## 🔐 Conformité Légale

### Robots.txt

Respecte le fichier `robots.txt` de chaque site :

```python
def can_scrape(url: str) -> bool:
    """Vérifie si le scraping est autorisé"""
    robot_parser = RobotFileParser()
    robot_parser.set_url(url + "/robots.txt")
    robot_parser.read()
    return robot_parser.can_fetch("*", url)
```

### Throttling

Respecte les délais entre les requêtes :

```python
# Délai minimum entre les requêtes par domaine
MIN_DELAY_BETWEEN_REQUESTS = 2  # secondes

# Délai minimum entre les requêtes globales
MIN_GLOBAL_DELAY = 0.5  # secondes
```

### RGPD

- ✅ Consentement utilisateur pour les alertes
- ✅ Droit à l'oubli (suppression des données)
- ✅ Transparence sur les sources
- ✅ Pas de stockage de données sensibles

---

## 🚀 Déploiement

### Services Requis

```yaml
services:
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: real_estate

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/real_estate
      REDIS_URL: redis://redis:6379/0

  celery:
    build: ./backend
    command: celery -A app.scraper.continuous_scraping worker
    depends_on:
      - postgres
      - redis
```

### Lancer l'Application

```bash
# Démarrer les services
docker compose up -d

# Initialiser la base de données
docker compose exec backend python -m alembic upgrade head

# Lancer le scraping
docker compose exec celery celery -A app.scraper.continuous_scraping worker
```

---

## 📈 Performances

### Capacités

- **Agences** : Jusqu'à 10,000+ agences
- **Annonces** : Jusqu'à 1,000,000+ annonces
- **Requêtes/seconde** : 100+ requêtes/s
- **Temps de réponse** : < 500ms (p95)

### Optimisations

- ✅ Index de base de données
- ✅ Cache Redis
- ✅ Elasticsearch pour la recherche
- ✅ Scraping parallèle
- ✅ Compression des données
- ✅ CDN pour les images

---

## 🔧 Configuration

### Variables d'Environnement

```bash
# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/real_estate

# Redis
REDIS_URL=redis://localhost:6379/0

# Google Maps API
GOOGLE_MAPS_API_KEY=your_api_key

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Proxies
PROXIES=http://proxy1:8080,http://proxy2:8080

# Scraping
MIN_DELAY_BETWEEN_REQUESTS=2
MAX_CONCURRENT_REQUESTS=10
SCRAPING_TIMEOUT=30
```

---

## 📚 API Endpoints

### Recherche

```
GET /api/listings/search?postal_code=75015&price_min=200000&price_max=500000
GET /api/listings/{id}
GET /api/listings/nearby?lat=48.8566&lng=2.3522&radius=5000
```

### Agences

```
GET /api/agencies?postal_code=75015
GET /api/agencies/{id}
GET /api/agencies/{id}/listings
```

### Utilisateur

```
POST /api/auth/register
POST /api/auth/login
GET /api/user/favorites
POST /api/user/favorites/{listing_id}
DELETE /api/user/favorites/{listing_id}
```

### Alertes

```
POST /api/user/alerts
GET /api/user/alerts
PUT /api/user/alerts/{alert_id}
DELETE /api/user/alerts/{alert_id}
```

### Statistiques

```
GET /api/statistics/market?postal_code=75015
GET /api/statistics/agencies
GET /api/statistics/listings
```

---

## 🎯 Cas d'Usage

### 1. Chercheur d'Appartement

```
1. S'enregistrer sur l'application
2. Créer une alerte : "Appartement 3 pièces, 75015, 200k-500k"
3. Recevoir des notifications email quand une annonce correspond
4. Ajouter les annonces intéressantes en favoris
5. Comparer les annonces favorites
```

### 2. Investisseur Immobilier

```
1. Analyser les statistiques du marché
2. Identifier les tendances de prix
3. Suivre les agences actives
4. Créer des alertes pour les bonnes affaires
5. Exporter les données pour analyse
```

### 3. Agence Immobilière

```
1. Voir les annonces de ses concurrents
2. Analyser les prix du marché
3. Identifier les opportunités
4. Surveiller la concurrence
```

---

## ✅ Checklist de Déploiement

- [ ] Base de données PostgreSQL configurée
- [ ] Redis configuré
- [ ] Google Maps API key obtenue
- [ ] Email SMTP configuré
- [ ] SMS Twilio configuré (optionnel)
- [ ] Variables d'environnement définies
- [ ] Proxies configurés
- [ ] Scraping lancé
- [ ] Monitoring configuré
- [ ] Alertes configurées
- [ ] Backups configurés
- [ ] SSL/TLS configuré
- [ ] CDN configuré
- [ ] Logs centralisés
- [ ] Monitoring des performances

---

## 📞 Support

Pour toute question ou problème :

1. Consulter la documentation
2. Vérifier les logs
3. Contacter le support technique
