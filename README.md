# Real Estate Scraper — Application de Scraping Immobilier

Application complète de scraping immobilier permettant de récupérer en temps réel les annonces des agences immobilières à partir d'un code postal français, avec respect des contraintes légales (robots.txt, RGPD, throttling).

## Architecture

```
real-estate-scraper/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── main.py         # Point d'entrée FastAPI
│   │   ├── models.py       # Modèles SQLAlchemy
│   │   ├── schemas.py      # Schémas Pydantic
│   │   ├── database.py     # Configuration BD
│   │   ├── routes/
│   │   │   ├── agencies.py # Endpoints agences
│   │   │   ├── listings.py # Endpoints annonces
│   │   │   └── search.py   # Endpoints recherche
│   │   └── scraper/
│   │       ├── scraper.py  # Logique de scraping
│   │       ├── parser.py   # Parsing HTML
│   │       └── legal.py    # Respect robots.txt, RGPD
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Application React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── .env.example
├── docker-compose.yml       # PostgreSQL + services
└── docs/                    # Documentation
```

## Stack Technique

- **Back-end** : FastAPI (Python 3.11)
- **Scraping** : BeautifulSoup4, requests, httpx
- **Base de données** : PostgreSQL + SQLAlchemy
- **Front-end** : React 19 + TypeScript + Vite
- **Containerisation** : Docker Compose

## Contraintes Légales Intégrées

✅ Respect du fichier `robots.txt` de chaque domaine  
✅ Throttling configurable (délais entre requêtes)  
✅ Gestion des erreurs réseau (429, 403, captchas)  
✅ Respect du RGPD (pas de données personnelles)  
✅ Commentaires rappelant la vérification des CGU  
✅ Configuration pour activer/désactiver les domaines  

## Installation Rapide

```bash
# 1. Cloner et entrer dans le répertoire
cd real-estate-scraper

# 2. Démarrer les services (PostgreSQL)
docker-compose up -d

# 3. Installer et lancer le back-end
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# 4. Installer et lancer le front-end (nouveau terminal)
cd frontend
npm install
npm run dev
```

L'application sera accessible sur `http://localhost:5173` (front-end) et l'API sur `http://localhost:8000`.

## Utilisation

1. Saisir un code postal français (ex : 75015)
2. L'application identifie les agences immobilières du secteur
3. Récupère leurs annonces en temps réel
4. Affiche les résultats filtrables par : prix, surface, type de bien, agence

## Fichiers Clés

- `backend/app/scraper/legal.py` — Gestion robots.txt, throttling, RGPD
- `backend/app/scraper/parser.py` — Extraction des données HTML
- `frontend/src/pages/Search.tsx` — Interface de recherche
- `docker-compose.yml` — Configuration des services
# Force rebuild - Sun Feb 22 09:06:35 EST 2026
