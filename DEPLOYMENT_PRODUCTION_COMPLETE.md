# Guide Complet de Déploiement Production

## 🎯 Objectif

Déployer l'application Real Estate Scraper en production avec haute disponibilité, performance optimale, et sécurité maximale.

---

## 📋 Checklist Pré-Déploiement

- [ ] Tests complets passés (test_complete.py)
- [ ] Variables d'environnement configurées
- [ ] Certificats SSL/TLS générés
- [ ] Base de données migrée
- [ ] Backups configurés
- [ ] Monitoring en place
- [ ] Alertes testées
- [ ] Logs centralisés
- [ ] CDN configuré
- [ ] Domaine DNS pointé

---

## 🐳 Déploiement Docker

### 1. **Préparation**

```bash
# Cloner le repository
git clone https://github.com/your-org/real-estate-scraper.git
cd real-estate-scraper

# Créer les fichiers d'environnement
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Éditer les fichiers .env avec les valeurs de production
nano backend/.env
nano frontend/.env
```

### 2. **Build Docker**

```bash
# Builder l'image backend
docker build -t real-estate-scraper-backend:latest backend/

# Builder l'image frontend
docker build -t real-estate-scraper-frontend:latest frontend/

# Tagger pour registry
docker tag real-estate-scraper-backend:latest your-registry/real-estate-scraper-backend:latest
docker tag real-estate-scraper-frontend:latest your-registry/real-estate-scraper-frontend:latest

# Push vers registry
docker push your-registry/real-estate-scraper-backend:latest
docker push your-registry/real-estate-scraper-frontend:latest
```

### 3. **Docker Compose Production**

```yaml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: real_estate
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend FastAPI
  backend:
    image: your-registry/real-estate-scraper-backend:latest
    environment:
      DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@postgres:5432/real_estate
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
      LOG_LEVEL: info
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Frontend React
  frontend:
    image: your-registry/real-estate-scraper-frontend:latest
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: https://api.yourdomain.com
    restart: unless-stopped

  # Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./alerts.yml:/etc/prometheus/alerts.yml:ro
      - prometheus_data:/prometheus
    restart: unless-stopped

  # AlertManager
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    restart: unless-stopped

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    image: your-registry/real-estate-scraper-backend:latest
    command: celery -A app.scraper.continuous_scraping worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@postgres:5432/real_estate
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # Celery Beat
  celery-beat:
    image: your-registry/real-estate-scraper-backend:latest
    command: celery -A app.scraper.continuous_scraping beat --loglevel=info
    environment:
      DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@postgres:5432/real_estate
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  alertmanager_data:
  grafana_data:
```

### 4. **Démarrer les services**

```bash
# Démarrer tous les services
docker compose up -d

# Vérifier les services
docker compose ps

# Voir les logs
docker compose logs -f backend
docker compose logs -f frontend

# Arrêter les services
docker compose down
```

---

## 🔒 Configuration SSL/TLS

### 1. **Générer les certificats**

```bash
# Utiliser Let's Encrypt avec Certbot
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Les certificats sont dans /etc/letsencrypt/live/yourdomain.com/
```

### 2. **Configuration Nginx**

```nginx
# nginx.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

# Redirection HTTP -> HTTPS
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS - API
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # CORS
    add_header Access-Control-Allow-Origin "https://yourdomain.com" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# HTTPS - Frontend
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 🗄️ Migration Base de Données

### 1. **Initialiser la BD**

```bash
# Se connecter au container backend
docker compose exec backend bash

# Créer les tables
python3 -c "from app.database import init_db; init_db()"

# Vérifier les tables
psql -h postgres -U app_user -d real_estate -c "\dt"
```

### 2. **Backup et Restore**

```bash
# Backup
docker compose exec postgres pg_dump -U app_user real_estate > backup.sql

# Restore
docker compose exec -T postgres psql -U app_user real_estate < backup.sql

# Backup automatique (cron)
0 2 * * * docker compose exec -T postgres pg_dump -U app_user real_estate > /backups/backup_$(date +\%Y\%m\%d).sql
```

---

## 📊 Configuration Monitoring

### 1. **Prometheus**

```bash
# Accès
http://yourdomain.com:9090

# Vérifier les targets
http://yourdomain.com:9090/targets
```

### 2. **Grafana**

```bash
# Accès
http://yourdomain.com:3001

# Ajouter Prometheus comme data source
# URL: http://prometheus:9090
```

### 3. **AlertManager**

```bash
# Accès
http://yourdomain.com:9093

# Vérifier les alertes
http://yourdomain.com:9093/#/alerts
```

---

## 🚀 Déploiement sur Heroku

### 1. **Préparation**

```bash
# Installer Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Créer l'app
heroku create real-estate-scraper

# Ajouter PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Ajouter Redis
heroku addons:create heroku-redis:premium-0
```

### 2. **Configuration**

```bash
# Variables d'environnement
heroku config:set SECRET_KEY=your_secret_key
heroku config:set ENVIRONMENT=production
heroku config:set LOG_LEVEL=info

# Vérifier
heroku config
```

### 3. **Deploy**

```bash
# Push vers Heroku
git push heroku main

# Voir les logs
heroku logs --tail

# Accès
https://real-estate-scraper.herokuapp.com
```

---

## 🌐 Déploiement sur AWS

### 1. **ECS (Elastic Container Service)**

```bash
# Créer un cluster
aws ecs create-cluster --cluster-name real-estate-scraper

# Créer une task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Créer un service
aws ecs create-service \
  --cluster real-estate-scraper \
  --service-name backend \
  --task-definition real-estate-scraper-backend \
  --desired-count 2 \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000
```

### 2. **RDS (Relational Database Service)**

```bash
# Créer une instance PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier real-estate-scraper-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username admin \
  --master-user-password your_password \
  --allocated-storage 100
```

### 3. **ElastiCache (Redis)**

```bash
# Créer un cluster Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id real-estate-scraper-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

---

## 🔄 Déploiement sur DigitalOcean

### 1. **App Platform**

```bash
# Créer l'app
doctl apps create --spec app.yaml

# Vérifier le statut
doctl apps list

# Voir les logs
doctl apps logs --app-id <app-id>
```

### 2. **Managed Database**

```bash
# Créer PostgreSQL
doctl databases create \
  --engine pg \
  --region nyc3 \
  --size db-s-1vcpu-1gb \
  real-estate-scraper-db
```

---

## 📈 Performance Optimization

### 1. **Caching**

```python
# Redis cache pour les listings
@app.get("/api/discovery/listings")
@cache(expire=3600)  # Cache 1 heure
async def get_listings(...):
    ...
```

### 2. **Database Indexing**

```sql
-- Créer des indexes
CREATE INDEX idx_listings_postal_code ON aggregated_listings(postal_code);
CREATE INDEX idx_listings_price ON aggregated_listings(price);
CREATE INDEX idx_listings_agency_id ON aggregated_listings(agency_id);
CREATE INDEX idx_agencies_postal_code ON agencies(postal_code);
```

### 3. **Connection Pooling**

```python
# Dans database.py
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## 🔐 Sécurité

### 1. **Secrets Management**

```bash
# Utiliser AWS Secrets Manager
aws secretsmanager create-secret \
  --name real-estate-scraper/db-password \
  --secret-string "your_password"
```

### 2. **Network Security**

```bash
# Security Group
aws ec2 create-security-group \
  --group-name real-estate-scraper-sg \
  --description "Real Estate Scraper Security Group"

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
  --group-name real-estate-scraper-sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 3. **WAF (Web Application Firewall)**

```bash
# Créer une Web ACL
aws wafv2 create-web-acl \
  --name real-estate-scraper-waf \
  --scope CLOUDFRONT \
  --default-action Block={}
```

---

## 📋 Checklist Post-Déploiement

- [ ] API accessible et fonctionnelle
- [ ] Frontend chargé correctement
- [ ] Base de données connectée
- [ ] Redis opérationnel
- [ ] Monitoring actif
- [ ] Alertes testées
- [ ] Logs collectés
- [ ] Backups automatiques
- [ ] SSL/TLS valide
- [ ] Performance acceptable (< 500ms)
- [ ] Taux d'erreur < 1%
- [ ] Uptime > 99.9%

---

## 🆘 Troubleshooting

### Problème : API indisponible

```bash
# Vérifier les logs
docker compose logs backend

# Vérifier la connexion BD
docker compose exec backend python3 -c "from app.database import SessionLocal; SessionLocal()"

# Redémarrer
docker compose restart backend
```

### Problème : Scraping échoue

```bash
# Vérifier les logs Celery
docker compose logs celery-worker

# Vérifier les tâches
docker compose exec redis redis-cli KEYS "celery*"

# Redémarrer Celery
docker compose restart celery-worker celery-beat
```

### Problème : Performance lente

```bash
# Vérifier les requêtes lentes
docker compose exec postgres psql -U app_user real_estate -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Analyser les indexes
docker compose exec postgres psql -U app_user real_estate -c "ANALYZE;"
```

---

## 📞 Support

Pour toute question, consultez :
- Documentation Docker : https://docs.docker.com/
- Documentation Nginx : https://nginx.org/en/docs/
- Documentation PostgreSQL : https://www.postgresql.org/docs/
- Documentation Heroku : https://devcenter.heroku.com/
- Documentation AWS : https://docs.aws.amazon.com/
