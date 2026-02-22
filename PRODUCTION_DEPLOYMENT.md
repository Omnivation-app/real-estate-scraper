# Guide de Déploiement Production

Guide complet pour déployer l'application Real Estate Scraper en production.

## 1. Préparation Pré-Déploiement

### Checklist de Sécurité

- [ ] Toutes les variables sensibles sont dans `.env` (pas en dur dans le code)
- [ ] `SECRET_KEY` est généré aléatoirement et sécurisé
- [ ] CORS est configuré correctement (domaines spécifiques, pas `*`)
- [ ] Rate limiting est activé
- [ ] HTTPS/SSL est configuré
- [ ] Authentification JWT est sécurisée
- [ ] Mots de passe sont hashés (bcrypt)
- [ ] Logs ne contiennent pas de données sensibles
- [ ] Base de données est sauvegardée régulièrement
- [ ] Monitoring et alertes sont en place

### Checklist de Performance

- [ ] Base de données est indexée correctement
- [ ] Caching est configuré (Redis)
- [ ] CDN est configuré pour les assets statiques
- [ ] Compression gzip est activée
- [ ] Images sont optimisées
- [ ] Lazy loading est implémenté
- [ ] Base de données est optimisée (queries, N+1 problems)

## 2. Déploiement sur Heroku

### Étape 1 : Préparer le projet

```bash
# Créer un compte Heroku
# https://www.heroku.com

# Installer Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Se connecter
heroku login
```

### Étape 2 : Créer l'application

```bash
cd /home/ubuntu/real-estate-scraper

# Créer l'app Heroku
heroku create real-estate-scraper

# Ajouter PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Ajouter Redis
heroku addons:create heroku-redis:premium-0
```

### Étape 3 : Configurer les variables d'environnement

```bash
# Ajouter les variables d'environnement
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set SMTP_SERVER="smtp.gmail.com"
heroku config:set SMTP_PORT="587"
heroku config:set SMTP_USER="your-email@gmail.com"
heroku config:set SMTP_PASSWORD="your-app-password"
heroku config:set TWILIO_ACCOUNT_SID="your-account-sid"
heroku config:set TWILIO_AUTH_TOKEN="your-auth-token"
heroku config:set TWILIO_PHONE_NUMBER="+1234567890"

# Vérifier les variables
heroku config
```

### Étape 4 : Créer Procfile

```bash
cat > /home/ubuntu/real-estate-scraper/Procfile << 'EOF'
web: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
worker: celery -A app.tasks worker --loglevel=info
beat: celery -A app.tasks beat --loglevel=info
EOF
```

### Étape 5 : Créer runtime.txt

```bash
cat > /home/ubuntu/real-estate-scraper/runtime.txt << 'EOF'
python-3.11.0
EOF
```

### Étape 6 : Déployer

```bash
# Ajouter les fichiers
git add .
git commit -m "Prepare for Heroku deployment"

# Déployer
git push heroku main

# Vérifier les logs
heroku logs --tail

# Ouvrir l'application
heroku open
```

## 3. Déploiement avec Docker

### Étape 1 : Créer Dockerfile

```bash
cat > /home/ubuntu/real-estate-scraper/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY backend/requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY backend/ .

# Exposer le port
EXPOSE 8000

# Démarrer l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

### Étape 2 : Créer docker-compose.yml

```bash
cat > /home/ubuntu/real-estate-scraper/docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: real_estate_scraper
      POSTGRES_USER: scraper
      POSTGRES_PASSWORD: secure_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://scraper:secure_password_here@db:5432/real_estate_scraper
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app

  celery:
    build: .
    command: celery -A app.tasks worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://scraper:secure_password_here@db:5432/real_estate_scraper
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis

  beat:
    build: .
    command: celery -A app.tasks beat --loglevel=info
    environment:
      DATABASE_URL: postgresql://scraper:secure_password_here@db:5432/real_estate_scraper
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
EOF
```

### Étape 3 : Déployer

```bash
# Construire et démarrer
docker-compose -f docker-compose.prod.yml up -d

# Vérifier les logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Arrêter
docker-compose -f docker-compose.prod.yml down
```

## 4. Déploiement sur AWS

### Étape 1 : Créer une instance EC2

```bash
# Lancer une instance Ubuntu 22.04
# t3.medium (2 vCPU, 4GB RAM)
# Ouvrir les ports 80, 443, 8000
```

### Étape 2 : Configurer le serveur

```bash
# Se connecter à l'instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer les dépendances
sudo apt install -y python3.11 python3-pip postgresql postgresql-contrib nginx supervisor

# Cloner le projet
git clone https://github.com/your-repo/real-estate-scraper.git
cd real-estate-scraper

# Installer les dépendances Python
pip install -r backend/requirements.txt

# Créer un utilisateur pour l'application
sudo useradd -m -s /bin/bash scraper
sudo chown -R scraper:scraper /home/ubuntu/real-estate-scraper
```

### Étape 3 : Configurer PostgreSQL

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer la base de données
CREATE DATABASE real_estate_scraper;
CREATE USER scraper WITH PASSWORD 'secure_password_here';
ALTER ROLE scraper SET client_encoding TO 'utf8';
ALTER ROLE scraper SET default_transaction_isolation TO 'read committed';
ALTER ROLE scraper SET default_transaction_deferrable TO on;
ALTER ROLE scraper SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE real_estate_scraper TO scraper;
\q
```

### Étape 4 : Configurer Supervisor

```bash
# Créer un fichier de configuration
sudo cat > /etc/supervisor/conf.d/real-estate-scraper.conf << 'EOF'
[program:real-estate-scraper]
directory=/home/ubuntu/real-estate-scraper/backend
command=/usr/bin/python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
user=scraper
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/real-estate-scraper.log
environment=DATABASE_URL="postgresql://scraper:secure_password_here@localhost:5432/real_estate_scraper"
EOF

# Redémarrer Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start real-estate-scraper
```

### Étape 5 : Configurer Nginx

```bash
# Créer un fichier de configuration
sudo cat > /etc/nginx/sites-available/real-estate-scraper << 'EOF'
upstream real_estate_scraper {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Certificate (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json;

    # Proxy settings
    location / {
        proxy_pass http://real_estate_scraper;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /home/ubuntu/real-estate-scraper/frontend/dist/;
        expires 30d;
    }
}
EOF

# Activer la configuration
sudo ln -s /etc/nginx/sites-available/real-estate-scraper /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Tester la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx
```

### Étape 6 : Configurer SSL avec Let's Encrypt

```bash
# Installer Certbot
sudo apt install -y certbot python3-certbot-nginx

# Générer le certificat
sudo certbot certonly --nginx -d your-domain.com

# Renouvellement automatique
sudo systemctl enable certbot.timer
```

## 5. Monitoring et Logging

### Prometheus + Grafana

```bash
# Installer Prometheus
docker run -d -p 9090:9090 \
  -v /home/ubuntu/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Installer Grafana
docker run -d -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```bash
# Installer Elasticsearch
docker run -d -p 9200:9200 \
  -e "discovery.type=single-node" \
  docker.elastic.co/elasticsearch/elasticsearch:8.0.0

# Installer Kibana
docker run -d -p 5601:5601 \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" \
  docker.elastic.co/kibana/kibana:8.0.0
```

## 6. Backups

### Backup PostgreSQL

```bash
# Backup manuel
pg_dump real_estate_scraper > backup.sql

# Backup automatisé (cron)
0 2 * * * pg_dump real_estate_scraper | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

### Backup S3

```bash
# Installer AWS CLI
pip install awscli

# Configurer AWS
aws configure

# Backup vers S3
aws s3 cp backup.sql s3://your-bucket/backups/
```

## 7. Scaling

### Horizontal Scaling

```bash
# Utiliser un load balancer (AWS ELB, Nginx)
# Déployer plusieurs instances de l'application
# Utiliser une base de données centralisée (RDS)
# Utiliser Redis pour le caching distribué
```

### Vertical Scaling

```bash
# Augmenter les ressources de l'instance
# Augmenter le nombre de workers Uvicorn
# Augmenter la taille du pool de connexions PostgreSQL
```

## 8. Troubleshooting

### Application ne démarre pas

```bash
# Vérifier les logs
sudo supervisorctl tail real-estate-scraper

# Vérifier les variables d'environnement
sudo supervisorctl -c /etc/supervisor/supervisord.conf

# Vérifier la base de données
psql -U scraper -d real_estate_scraper -c "SELECT 1;"
```

### Lenteur de l'application

```bash
# Vérifier les ressources
top
free -h
df -h

# Vérifier les queries lentes
# Ajouter logging SQL dans app/main.py
echo "SQL_ECHO=true" >> .env

# Vérifier le cache Redis
redis-cli INFO
```

### Erreurs de connexion à la base de données

```bash
# Vérifier la connexion PostgreSQL
psql -U scraper -d real_estate_scraper -h localhost

# Vérifier les variables d'environnement
echo $DATABASE_URL

# Vérifier les logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql.log
```

## 9. Ressources

- [Heroku Documentation](https://devcenter.heroku.com/)
- [Docker Documentation](https://docs.docker.com/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
