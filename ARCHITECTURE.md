# Architecture — Real Estate Scraper

## Vue d'ensemble

L'application Real Estate Scraper est une solution complète pour scraper, stocker et visualiser les annonces immobilières françaises. Elle respecte les contraintes légales (robots.txt, RGPD, throttling) et offre une interface intuitive pour rechercher des propriétés.

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  - Interface de recherche avec filtres                       │
│  - Affichage des résultats en grille                         │
│  - Gestion des agences immobilières                          │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Python 3.11)                 │
│  - Routes API (listings, agencies, scraper)                 │
│  - Gestion de la base de données (SQLAlchemy ORM)           │
│  - Module de scraping avec conformité légale                │
└─────────────────────┬───────────────────────────────────────┘
                      │ SQL
                      ↓
┌─────────────────────────────────────────────────────────────┐
│           Database (PostgreSQL 16)                           │
│  - Agences immobilières                                      │
│  - Annonces immobilières                                     │
│  - Logs de scraping                                          │
│  - Configuration des domaines                                │
└─────────────────────────────────────────────────────────────┘
```

## Composants Principaux

### 1. Frontend (React + Vite)

**Localisation :** `/frontend`

**Responsabilités :**
- Interface utilisateur pour la recherche d'annonces
- Filtres avancés (prix, surface, type de bien, agence)
- Affichage des résultats en grille responsive
- Intégration avec l'API backend via axios

**Fichiers clés :**
- `src/pages/Search.tsx` — Page de recherche principale
- `src/services/api.ts` — Client API pour communiquer avec le backend
- `src/App.tsx` — Composant racine
- `vite.config.ts` — Configuration Vite

### 2. Backend (FastAPI)

**Localisation :** `/backend`

**Responsabilités :**
- API REST pour les annonces, agences et scraping
- Gestion de la base de données
- Orchestration du scraping
- Respect des contraintes légales

**Structure :**
```
backend/app/
├── main.py              # Application FastAPI
├── models.py            # Modèles SQLAlchemy
├── schemas.py           # Schémas Pydantic
├── database.py          # Configuration BD
├── routes/
│   ├── agencies.py      # Routes pour les agences
│   ├── listings.py      # Routes pour les annonces
│   └── scraper.py       # Routes pour le scraping
└── scraper/
    ├── scraper.py       # Logique principale de scraping
    ├── parser.py        # Parsing HTML
    ├── legal.py         # Conformité légale
    └── __init__.py
```

### 3. Module de Scraping

**Localisation :** `/backend/app/scraper`

**Composants :**

#### `scraper.py` — Orchestration
Responsable de :
- Identifier les agences immobilières pour un code postal
- Récupérer les annonces de chaque agence
- Extraire les informations légales des agences
- Gérer les erreurs et les retries

#### `parser.py` — Extraction de données
Responsable de :
- Parser le HTML des pages d'annonces
- Extraire les informations de chaque listing
- Extraire les mentions légales des agences
- Normaliser les données

#### `legal.py` — Conformité légale
Responsable de :
- Vérifier le fichier `robots.txt` avant le scraping
- Appliquer le throttling (délais entre requêtes)
- Gérer le rate limiting (max requêtes/heure)
- Respecter le RGPD (pas de données personnelles)
- Gérer les erreurs HTTP (429, 403, captchas)

### 4. Base de Données

**Localisation :** PostgreSQL 16 (Docker)

**Modèles :**

#### `Agency`
Représente une agence immobilière avec ses informations légales.

Champs :
- `id` — Identifiant unique
- `legal_name` — Raison sociale
- `website_url` — URL du site (unique)
- `postal_address` — Adresse postale
- `postal_code` — Code postal
- `city` — Ville
- `phone` — Téléphone
- `siren` — Numéro SIREN
- `siret` — Numéro SIRET
- `professional_card` — Numéro de carte professionnelle
- `last_scraped` — Dernière date de scraping
- `is_active` — Statut actif/inactif

#### `Listing`
Représente une annonce immobilière.

Champs :
- `id` — Identifiant unique
- `external_id` — ID externe (du site source)
- `agency_id` — Référence à l'agence
- `title` — Titre de l'annonce
- `description` — Description
- `property_type` — Type de bien (apartment, house, land, commercial, other)
- `operation_type` — Type d'opération (sale, rental)
- `price` — Prix
- `surface_area` — Surface en m²
- `number_of_rooms` — Nombre de pièces
- `number_of_bedrooms` — Nombre de chambres
- `city` — Ville
- `postal_code` — Code postal
- `district` — Quartier
- `address_partial` — Adresse partielle
- `listing_url` — URL de l'annonce (unique)
- `image_urls` — URLs des images (JSON)
- `posted_date` — Date de publication
- `created_at` — Date de création en BD
- `last_updated` — Date de dernière mise à jour

#### `ScrapingLog`
Trace les opérations de scraping.

Champs :
- `id` — Identifiant unique
- `domain` — Domaine scrapé
- `status` — Statut (success, error, blocked, throttled)
- `message` — Message de log
- `listings_count` — Nombre d'annonces trouvées
- `agencies_count` — Nombre d'agences trouvées
- `execution_time` — Temps d'exécution en secondes
- `created_at` — Date du log

#### `DomainConfig`
Configuration pour activer/désactiver le scraping par domaine.

Champs :
- `id` — Identifiant unique
- `domain` — Domaine (ex: seloger.com)
- `is_enabled` — Scraping activé/désactivé
- `throttle_delay` — Délai minimum entre requêtes (secondes)
- `max_requests_per_hour` — Limite de requêtes par heure
- `respect_robots_txt` — Respecter robots.txt
- `notes` — Notes

## Flux de Données

### 1. Recherche d'annonces

```
Frontend
  ↓ (GET /api/listings/)
Backend (listingsAPI.search)
  ↓ (Query)
PostgreSQL
  ↓ (Résultats)
Backend (Response)
  ↓ (JSON)
Frontend (Affichage)
```

### 2. Scraping

```
Frontend (POST /api/scraper/scrape-postal-code/{postal_code})
  ↓
Backend (Background Task)
  ├─ Identifier les agences
  ├─ Pour chaque agence :
  │  ├─ Vérifier robots.txt
  │  ├─ Attendre throttle_delay
  │  ├─ Récupérer les annonces
  │  ├─ Parser les données
  │  └─ Sauvegarder en BD
  └─ Enregistrer le log
```

### 3. Conformité Légale

```
Avant chaque requête :
  ├─ Vérifier robots.txt
  ├─ Vérifier rate limit
  ├─ Attendre throttle_delay
  └─ Effectuer la requête

En cas d'erreur :
  ├─ 429 (Too Many Requests) → Augmenter throttle_delay, bloquer temporairement
  ├─ 403 (Forbidden) → Vérifier captcha, bloquer si nécessaire
  ├─ 500 (Server Error) → Augmenter throttle_delay
  └─ Timeout → Augmenter throttle_delay
```

## Endpoints API

### Listings
- `GET /api/listings/` — Rechercher avec filtres
- `GET /api/listings/{id}` — Récupérer une annonce
- `GET /api/listings/by-postal-code/{postal_code}` — Annonces par code postal
- `GET /api/listings/stats/by-postal-code/{postal_code}` — Statistiques

### Agencies
- `GET /api/agencies/` — Lister les agences
- `GET /api/agencies/{id}` — Récupérer une agence
- `GET /api/agencies/by-postal-code/{postal_code}` — Agences par code postal
- `GET /api/agencies/{id}/listings` — Annonces d'une agence
- `POST /api/agencies/` — Créer une agence
- `PUT /api/agencies/{id}` — Mettre à jour une agence
- `DELETE /api/agencies/{id}` — Supprimer une agence

### Scraper
- `POST /api/scraper/scrape-postal-code/{postal_code}` — Lancer le scraping
- `GET /api/scraper/logs` — Récupérer les logs
- `GET /api/scraper/logs/{domain}` — Logs par domaine

### Health
- `GET /health` — Santé de l'API
- `GET /api/info` — Informations sur l'API

## Conformité Légale

### Respect de robots.txt
- Chaque domaine a un `robots.txt` qui définit les règles de scraping
- Le module `legal.py` vérifie ces règles avant chaque requête
- Les URLs non autorisées sont ignorées

### Throttling
- Délai configurable entre les requêtes (défaut : 2 secondes)
- Peut être ajusté par domaine via `DomainConfig`
- Augmente automatiquement en cas d'erreur

### Rate Limiting
- Maximum 100 requêtes par heure par domaine (configurable)
- Suivi via les timestamps des requêtes
- Blocage temporaire (1 heure) si dépassement

### RGPD
- Pas de collecte de données personnelles (emails, téléphones, etc.)
- Seules les données publiques des annonces sont collectées
- Mentions légales des agences (SIREN, SIRET) sont collectées

### Configuration par Domaine
- Table `DomainConfig` permet d'activer/désactiver le scraping
- Configuration du throttle_delay et du rate limit
- Notes sur chaque domaine

## Déploiement

### Développement

```bash
# 1. Démarrer PostgreSQL
docker-compose up -d

# 2. Démarrer le backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# 3. Démarrer le frontend (nouveau terminal)
cd frontend
npm install
npm run dev
```

### Production

À implémenter :
- Docker images pour backend et frontend
- Docker Compose pour l'orchestration
- Configuration des variables d'environnement
- SSL/TLS
- Load balancing
- Monitoring et logging

## Performance et Optimisations

### Actuelles
- Pagination des résultats (limit/offset)
- Indexation des colonnes clés (postal_code, price, etc.)
- Connection pooling pour la BD

### À implémenter
- Cache Redis pour les résultats fréquents
- Compression des images
- Lazy loading des images
- Optimisation des requêtes SQL
- CDN pour les assets statiques

## Sécurité

### Actuelles
- CORS configuré
- Validation des entrées (Pydantic)
- Paramètres de requête validés

### À implémenter
- Authentification (JWT)
- Autorisation (roles)
- Rate limiting côté API
- Sanitization des données
- Logging des accès
- Audit trail

## Monitoring et Logging

### Actuelles
- Logs de scraping dans `ScrapingLog`
- Logs FastAPI (stdout)

### À implémenter
- Centralization des logs (ELK, Datadog)
- Monitoring des performances
- Alertes en cas d'erreur
- Dashboard de santé
