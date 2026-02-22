# Deployment Guide — Real Estate Scraper

Guide complet pour déployer l'application Real Estate Scraper en production.

## Architecture de Déploiement

```
┌─────────────────────────────────────────────────────────┐
│                    CDN / Static Files                    │
│              (CloudFlare, AWS S3, etc.)                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Load Balancer / Reverse Proxy               │
│           (Nginx, HAProxy, AWS ALB, etc.)                │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┬─────────────────┐
        ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Backend 1   │  │  Backend 2   │  │  Backend 3   │
│  (FastAPI)   │  │  (FastAPI)   │  │  (FastAPI)   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┬─────────────────┘
                          ↓
                ┌──────────────────┐
                │   PostgreSQL     │
                │  (Replicated)    │
                └──────────────────┘
```

## Déploiement sur Heroku

### Prérequis

- Compte Heroku
- Heroku CLI installé
- Git configuré

### Étapes

1. **Créer l'application Heroku**

```bash
heroku create real-estate-scraper
```

2. **Ajouter PostgreSQL**

```bash
heroku addons:create heroku-postgresql:standard-0 -a real-estate-scraper
```

3. **Configurer les variables d'environnement**

```bash
heroku config:set DATABASE_URL=<auto-configured> -a real-estate-scraper
heroku config:set ENVIRONMENT=production -a real-estate-scraper
heroku config:set LOG_LEVEL=INFO -a real-estate-scraper
```

4. **Créer un Procfile**

```
web: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. **Déployer**

```bash
git push heroku main
```

6. **Initialiser la base de données**

```bash
heroku run "cd backend && python -c 'from app.database import init_db; init_db()'" -a real-estate-scraper
```

## Déploiement avec Docker

### 1. Créer les images Docker

#### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY backend/app ./app

# Créer les tables
RUN python -c "from app.database import init_db; init_db()" || true

# Démarrer le serveur
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 2. Docker Compose pour Production

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: real_estate_scraper
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/real_estate_scraper
      ENVIRONMENT: production
      LOG_LEVEL: INFO
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    environment:
      VITE_API_URL: http://backend:8000
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 3. Déployer avec Docker Compose

```bash
# Créer le fichier .env
cat > .env << EOF
DB_USER=postgres
DB_PASSWORD=secure_password_here
EOF

# Démarrer les services
docker-compose -f docker-compose.prod.yml up -d

# Vérifier le statut
docker-compose ps
```

## Déploiement sur AWS

### Avec ECS (Elastic Container Service)

1. **Créer un cluster ECS**

```bash
aws ecs create-cluster --cluster-name real-estate-scraper
```

2. **Créer les task definitions**

Voir les fichiers Dockerfile ci-dessus.

3. **Créer les services**

```bash
aws ecs create-service \
  --cluster real-estate-scraper \
  --service-name backend \
  --task-definition backend:1 \
  --desired-count 3 \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000
```

### Avec Elastic Beanstalk

1. **Initialiser Elastic Beanstalk**

```bash
eb init -p docker real-estate-scraper
```

2. **Créer l'environnement**

```bash
eb create real-estate-scraper-prod
```

3. **Déployer**

```bash
eb deploy
```

## Déploiement sur DigitalOcean

### Avec App Platform

1. **Connecter le repository GitHub**
2. **Configurer le build**
   - Backend : `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Frontend : `cd frontend && npm run build`
3. **Ajouter PostgreSQL**
4. **Configurer les variables d'environnement**
5. **Déployer**

## Configuration de Production

### Variables d'Environnement Essentielles

```env
# Base de données
DATABASE_URL=postgresql://user:password@host:5432/real_estate_scraper

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Sécurité
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# CORS
CORS_ORIGINS=https://yourdomain.com

# Scraping
SCRAPER_THROTTLE_DELAY=3.0
SCRAPER_MAX_REQUESTS_PER_HOUR=50
SCRAPER_RESPECT_ROBOTS_TXT=true

# Email (optionnel)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### SSL/TLS

1. **Avec Let's Encrypt**

```bash
# Nginx
sudo certbot certonly --nginx -d yourdomain.com

# Renouvellement automatique
sudo systemctl enable certbot.timer
```

2. **Avec AWS Certificate Manager**

```bash
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS
```

### Monitoring et Logging

1. **Logs centralisés (ELK Stack)**

```bash
# Elasticsearch
docker run -d -p 9200:9200 docker.elastic.co/elasticsearch/elasticsearch:8.0.0

# Logstash
docker run -d -p 5000:5000 docker.elastic.co/logstash/logstash:8.0.0

# Kibana
docker run -d -p 5601:5601 docker.elastic.co/kibana/kibana:8.0.0
```

2. **Monitoring (Prometheus + Grafana)**

```bash
# Prometheus
docker run -d -p 9090:9090 prom/prometheus

# Grafana
docker run -d -p 3000:3000 grafana/grafana
```

3. **Alertes (Sentry)**

```bash
pip install sentry-sdk
```

## Checklist de Déploiement

- [ ] Base de données configurée et testée
- [ ] Variables d'environnement définies
- [ ] SSL/TLS configuré
- [ ] CORS configuré correctement
- [ ] Logging centralisé en place
- [ ] Monitoring et alertes configurés
- [ ] Backups automatiques activés
- [ ] CDN configuré pour les assets statiques
- [ ] Rate limiting configuré
- [ ] Authentification sécurisée
- [ ] Tests de charge effectués
- [ ] Documentation de déploiement mise à jour

## Maintenance

### Backups

```bash
# PostgreSQL
pg_dump -U postgres real_estate_scraper > backup.sql

# Restauration
psql -U postgres real_estate_scraper < backup.sql
```

### Mises à jour

```bash
# Mettre à jour les dépendances
pip install --upgrade -r requirements.txt
npm update

# Tester
python -m pytest
npm test

# Déployer
git push heroku main
```

### Monitoring de la Santé

```bash
# Vérifier les logs
heroku logs -t

# Vérifier les métriques
heroku metrics
```

## Troubleshooting

### La base de données ne se connecte pas

Vérifier la `DATABASE_URL` et les credentials.

### L'API est lente

- Vérifier les logs
- Analyser les requêtes SQL lentes
- Ajouter des indexes
- Augmenter les ressources

### Le scraping échoue

- Vérifier les logs de scraping
- Augmenter le throttle_delay
- Vérifier les robots.txt
- Vérifier les CGU des sites

## Support

Pour plus d'aide, consultez la documentation officielle des services utilisés.
