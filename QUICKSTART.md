# Quick Start — Real Estate Scraper

Démarrez l'application Real Estate Scraper en quelques minutes.

## Prérequis

- Python 3.11+
- Node.js 18+ (pour le front-end)
- PostgreSQL 16 (optionnel, SQLite utilisé par défaut en développement)

## Installation Rapide

### 1. Cloner le projet

```bash
cd /home/ubuntu/real-estate-scraper
```

### 2. Démarrer le Back-end (FastAPI)

```bash
# Terminal 1
cd backend

# Installer les dépendances
pip install -r requirements.txt

# Démarrer le serveur (SQLite sera utilisé par défaut)
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera disponible sur `http://localhost:8000`

Documentation interactive : `http://localhost:8000/docs`

### 3. Démarrer le Front-end (React)

```bash
# Terminal 2
cd frontend

# Installer les dépendances
npm install

# Démarrer le serveur de développement
npm run dev
```

Le front-end sera disponible sur `http://localhost:5173`

## Utilisation

### Via l'Interface Web

1. Ouvrir `http://localhost:5173` dans votre navigateur
2. Entrer un code postal français (ex: 75015)
3. Cliquer sur "Scrape Now" pour récupérer les annonces
4. Utiliser les filtres pour affiner la recherche

### Via l'API

#### Rechercher des annonces

```bash
curl "http://localhost:8000/api/listings/?postal_code=75015&price_max=500000"
```

#### Lancer le scraping

```bash
curl -X POST "http://localhost:8000/api/scraper/scrape-postal-code/75015"
```

#### Récupérer les agences

```bash
curl "http://localhost:8000/api/agencies/by-postal-code/75015"
```

#### Voir la documentation complète

Accédez à `http://localhost:8000/docs` pour la documentation interactive Swagger.

## Configuration

### Variables d'Environnement

#### Back-end (`backend/.env`)

```env
# Base de données (SQLite par défaut)
DATABASE_URL=sqlite:///./real_estate_scraper.db

# PostgreSQL (optionnel)
# DATABASE_URL=postgresql://user:password@localhost:5432/real_estate_scraper

# Logging
SQL_ECHO=false
LOG_LEVEL=INFO

# Scraping
SCRAPER_THROTTLE_DELAY=2.0
SCRAPER_MAX_REQUESTS_PER_HOUR=100
SCRAPER_RESPECT_ROBOTS_TXT=true
```

#### Front-end (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=10000
```

## Déploiement avec Docker

### Démarrer PostgreSQL

```bash
docker-compose up -d
```

### Configurer le back-end pour PostgreSQL

Modifier `backend/.env` :

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/real_estate_scraper
```

Puis redémarrer le serveur.

## Endpoints Disponibles

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

### Scraper
- `POST /api/scraper/scrape-postal-code/{postal_code}` — Lancer le scraping
- `GET /api/scraper/logs` — Récupérer les logs
- `GET /api/scraper/logs/{domain}` — Logs par domaine

### Health
- `GET /health` — Santé de l'API
- `GET /api/info` — Informations sur l'API

## Conformité Légale

L'application respecte automatiquement :

✅ **robots.txt** — Chaque domaine est vérifié avant le scraping  
✅ **Throttling** — Délais configurables entre les requêtes  
✅ **Rate Limiting** — Maximum 100 requêtes/heure par domaine  
✅ **RGPD** — Pas de collecte de données personnelles  

## Troubleshooting

### Le back-end ne démarre pas

**Erreur :** `ModuleNotFoundError: No module named 'MySQLdb'`

**Solution :** Assurez-vous que `DATABASE_URL` n'est pas définie ou utilisez SQLite :

```bash
unset DATABASE_URL
python3 -m uvicorn app.main:app --reload
```

### Le front-end ne se connecte pas à l'API

**Vérifier :**
1. Le back-end est en cours d'exécution sur `http://localhost:8000`
2. La variable `VITE_API_URL` dans `frontend/.env` est correcte
3. CORS est activé dans le back-end

### La base de données SQLite n'existe pas

Elle sera créée automatiquement au premier démarrage du serveur.

## Prochaines Étapes

- Ajouter l'authentification utilisateur
- Implémenter la persistance des favoris
- Ajouter les notifications par email
- Déployer sur un serveur de production
- Ajouter plus de sources de scraping

## Support

Pour plus d'informations, consultez :
- `README.md` — Vue d'ensemble du projet
- `ARCHITECTURE.md` — Architecture technique
- `TODO.md` — Tâches en cours et prévues
