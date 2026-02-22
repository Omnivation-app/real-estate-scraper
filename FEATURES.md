# Fonctionnalités Avancées — Real Estate Scraper

Guide complet des 5 fonctionnalités avancées implémentées.

## 1. Sources Multiples de Scraping

### Sources Supportées

L'application peut scraper les annonces de plusieurs sources :

| Source | URL | Statut |
|--------|-----|--------|
| SeLoger | seloger.com | ✅ Implémenté |
| LeBonCoin | leboncoin.fr | ✅ Implémenté |
| Immobilier.com | immobilier.com | ✅ Implémenté |
| Orpi | orpi.com | ✅ Implémenté |
| Century21 | century21.fr | ✅ Implémenté |
| Foncia | foncia.com | ✅ Implémenté |

### Architecture Multi-Sources

```python
from app.scraper.sources import SourceRegistry

# Obtenir toutes les sources
sources = SourceRegistry.get_all_sources()

# Obtenir une source spécifique
seloger = SourceRegistry.get_source("seloger")

# Lister les sources disponibles
available = SourceRegistry.list_sources()
# ['seloger', 'leboncoin', 'immobilier.com', 'orpi', 'century21', 'foncia']
```

### Ajouter une Nouvelle Source

```python
from app.scraper.sources import RealEstateSource, SourceRegistry

class MyAgencySource(RealEstateSource):
    def __init__(self):
        super().__init__("MyAgency", "https://www.myagency.com")
    
    def build_search_url(self, postal_code: str) -> str:
        return f"https://www.myagency.com/search?postal_code={postal_code}"
    
    def extract_agency_info(self) -> dict:
        return {
            "legal_name": "My Agency",
            "website_url": self.website_url,
            "siren": "123456789",
        }

# Enregistrer la nouvelle source
SourceRegistry.register_source("myagency", MyAgencySource)
```

### Scraping Multi-Sources

```bash
# Scraper toutes les sources pour un code postal
curl -X POST "http://localhost:8000/api/scraper/scrape-postal-code/75015"

# Résultat
{
  "postal_code": "75015",
  "sources": {
    "seloger": {
      "status": "success",
      "listings_count": 45,
      "agencies_count": 12
    },
    "leboncoin": {
      "status": "success",
      "listings_count": 23,
      "agencies_count": 8
    },
    ...
  }
}
```

## 2. Authentification et Favoris

### Enregistrement Utilisateur

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "john_doe",
    "password": "secure_password_123",
    "full_name": "John Doe"
  }'

# Réponse
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "full_name": "John Doe",
  "is_active": true
}
```

### Connexion

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password_123"
  }'

# Réponse
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Ajouter aux Favoris

```bash
curl -X POST "http://localhost:8000/api/user/favorites/123" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Réponse
{
  "id": 1,
  "listing_id": 123,
  "created_at": "2026-02-21T19:54:24.659394"
}
```

### Récupérer les Favoris

```bash
curl "http://localhost:8000/api/user/favorites" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Réponse
[
  {
    "id": 1,
    "listing_id": 123,
    "created_at": "2026-02-21T19:54:24.659394"
  },
  {
    "id": 2,
    "listing_id": 456,
    "created_at": "2026-02-21T19:55:10.123456"
  }
]
```

### Supprimer des Favoris

```bash
curl -X DELETE "http://localhost:8000/api/user/favorites/123" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Réponse
{
  "message": "Favorite removed successfully"
}
```

## 3. Notifications Email/SMS

### Créer une Alerte de Recherche

```bash
curl -X POST "http://localhost:8000/api/user/alerts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Appartements 75015 < 500k",
    "postal_code": "75015",
    "min_price": 0,
    "max_price": 500000,
    "min_surface": 50,
    "property_type": "apartment"
  }'

# Réponse
{
  "id": 1,
  "name": "Appartements 75015 < 500k",
  "postal_code": "75015",
  "min_price": 0,
  "max_price": 500000,
  "min_surface": 50,
  "property_type": "apartment",
  "is_active": true,
  "created_at": "2026-02-21T19:54:24.659394"
}
```

### Récupérer les Alertes

```bash
curl "http://localhost:8000/api/user/alerts" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Configuration Email

Ajouter à `backend/.env` :

```env
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@realestate-scraper.com
```

**Note :** Pour Gmail, utiliser un [mot de passe d'application](https://support.google.com/accounts/answer/185833).

### Configuration SMS (Twilio)

Ajouter à `backend/.env` :

```env
# Twilio Configuration
SMS_API_KEY=your_twilio_api_key
SMS_API_URL=https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json
```

### Notifications Automatiques

Les notifications sont envoyées automatiquement quand :
- Une nouvelle annonce correspond à une alerte active
- L'utilisateur a activé les notifications email/SMS

### Exemple de Notification Email

```
Subject: [Real Estate] 3 nouvelle(s) annonce(s) pour Appartements 75015 < 500k

Bonjour John Doe,

Nous avons trouvé 3 nouvelle(s) annonce(s) correspondant à votre alerte de recherche.

1. Bel appartement 2 pièces
   Prix: 450,000€
   Surface: 65 m²
   Localisation: 75015 Paris
   Type: Apartment
   [Voir l'annonce]

2. Studio rénové
   Prix: 380,000€
   Surface: 35 m²
   Localisation: 75015 Paris
   Type: Apartment
   [Voir l'annonce]

...

[Gérer mes alertes]
```

## 4. Géolocalisation et Cartes Interactives

### Afficher une Carte des Annonces

```bash
# Carte HTML interactive
curl "http://localhost:8000/api/maps/listings-map/75015" > map.html
# Ouvrir map.html dans un navigateur
```

### Afficher une Carte des Agences

```bash
curl "http://localhost:8000/api/maps/agencies-map/75015" > agencies_map.html
```

### Trouver les Annonces à Proximité

```bash
# Trouver toutes les annonces dans un rayon de 5 km
curl "http://localhost:8000/api/maps/nearby-listings?lat=48.8566&lon=2.3522&radius_km=5"

# Réponse
[
  {
    "id": 1,
    "title": "Bel appartement 2 pièces",
    "price": 450000,
    "surface_area": 65,
    "city": "Paris",
    "postal_code": "75015",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "distance_km": 0.0,
    "listing_url": "https://..."
  },
  {
    "id": 2,
    "title": "Studio rénové",
    "price": 380000,
    "surface_area": 35,
    "city": "Paris",
    "postal_code": "75015",
    "latitude": 48.8570,
    "longitude": 2.3525,
    "distance_km": 0.56,
    "listing_url": "https://..."
  }
]
```

### Calculer la Distance Entre Deux Points

```bash
curl "http://localhost:8000/api/maps/distance?lat1=48.8566&lon1=2.3522&lat2=48.8570&lon2=2.3525"

# Réponse
{
  "distance_km": 0.56,
  "point1": {
    "latitude": 48.8566,
    "longitude": 2.3522
  },
  "point2": {
    "latitude": 48.8570,
    "longitude": 2.3525
  }
}
```

### Géolocalisation Automatique

Les annonces et agences sont géolocalisées automatiquement lors du scraping :

```python
from app.geolocation import geo_service

# Géolocaliser une annonce
listing = db.query(Listing).first()
if geo_service.geocode_listing(listing):
    print(f"Listing at {listing.latitude}, {listing.longitude}")
    db.commit()

# Géolocaliser une agence
agency = db.query(Agency).first()
if geo_service.geocode_agency(agency):
    print(f"Agency at {agency.latitude}, {agency.longitude}")
    db.commit()
```

### Carte Interactive (Folium)

Les cartes utilisent Folium (basé sur Leaflet.js) :

- **Marqueurs colorés** selon le prix (vert < 200k, bleu 200-500k, rouge > 500k)
- **Popups** avec informations de l'annonce
- **Zoom et pan** interactifs
- **Contrôle des couches** pour afficher/masquer les éléments

## 5. Déploiement Production

### Configuration Production

Créer un fichier `.env.production` :

```env
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>

# Database
DATABASE_URL=postgresql://user:password@host:5432/real_estate_scraper

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SMS (optionnel)
SMS_API_KEY=your_twilio_api_key
```

### Déploiement Docker

```bash
# Build les images
docker build -f backend/Dockerfile -t real-estate-backend:latest backend/
docker build -f frontend/Dockerfile -t real-estate-frontend:latest frontend/

# Démarrer les services
docker-compose -f docker-compose.prod.yml up -d

# Vérifier les logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Déploiement sur Heroku

```bash
# Créer l'application
heroku create real-estate-scraper

# Ajouter PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Configurer les variables d'environnement
heroku config:set SECRET_KEY=<your-secret-key>
heroku config:set SMTP_USER=<your-email>
heroku config:set SMTP_PASSWORD=<your-password>

# Déployer
git push heroku main

# Initialiser la base de données
heroku run "cd backend && python -c 'from app.database import init_db; init_db()'"
```

### Déploiement sur AWS

Voir `DEPLOYMENT.md` pour les instructions complètes.

### Monitoring

```bash
# Vérifier la santé de l'API
curl https://yourdomain.com/health

# Voir les logs
docker-compose logs -f backend

# Monitoring avec Prometheus
docker run -d -p 9090:9090 prom/prometheus

# Monitoring avec Grafana
docker run -d -p 3000:3000 grafana/grafana
```

## Checklist d'Intégration

- [ ] Sources multiples configurées et testées
- [ ] Authentification JWT fonctionnelle
- [ ] Favoris sauvegardés et récupérables
- [ ] Alertes de recherche créées et gérées
- [ ] Notifications email configurées et testées
- [ ] Notifications SMS configurées (optionnel)
- [ ] Cartes interactives affichées correctement
- [ ] Géolocalisation automatique en place
- [ ] Base de données PostgreSQL en production
- [ ] SSL/TLS configuré
- [ ] Monitoring et alertes en place
- [ ] Documentation mise à jour
- [ ] Tests unitaires passés
- [ ] Performance testée sous charge

## Support et Troubleshooting

### Les notifications ne s'envoient pas

1. Vérifier la configuration SMTP dans `.env`
2. Vérifier les logs : `docker-compose logs backend`
3. Tester la connexion SMTP :

```python
import smtplib
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login("your-email@gmail.com", "your-password")
print("SMTP connection successful!")
```

### Les cartes ne s'affichent pas

1. Vérifier que Folium est installé : `pip install folium`
2. Vérifier que les annonces ont des coordonnées (latitude/longitude)
3. Vérifier la console du navigateur pour les erreurs JavaScript

### L'authentification échoue

1. Vérifier le token JWT : `curl http://localhost:8000/api/auth/me -H "Authorization: Bearer YOUR_TOKEN"`
2. Vérifier que le SECRET_KEY est configuré
3. Vérifier l'expiration du token (30 minutes par défaut)

## Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [JWT Authentication](https://tools.ietf.org/html/rfc7519)
- [Folium Maps](https://folium.readthedocs.io/)
- [Geopy Geocoding](https://geopy.readthedocs.io/)
- [Twilio SMS](https://www.twilio.com/docs/sms)
