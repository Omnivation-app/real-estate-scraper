# Guide de Déploiement en Staging avec Docker

Guide complet pour déployer l'application Real Estate Scraper en environnement de staging avec Docker Compose.

## 1. Prérequis

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Git
- 4GB RAM minimum
- 10GB d'espace disque

### Installer Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ajouter votre utilisateur au groupe docker
sudo usermod -aG docker $USER
newgrp docker

# Vérifier l'installation
docker --version
docker compose version
```

## 2. Préparation du Projet

### Cloner le projet

```bash
git clone https://github.com/your-repo/real-estate-scraper.git
cd real-estate-scraper
```

### Créer le fichier .env.staging

```bash
cat > .env.staging << 'EOF'
# === DATABASE ===
POSTGRES_DB=real_estate_scraper
POSTGRES_USER=scraper
POSTGRES_PASSWORD=staging_password_change_me

# === EMAIL ===
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-password
FROM_EMAIL=your-email@gmail.com

# === TWILIO ===
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# === API ===
SECRET_KEY=staging-secret-key-change-in-production
DEBUG=False
EOF
```

## 3. Déploiement en Staging

### Étape 1 : Construire les images Docker

```bash
# Construire l'image backend
docker compose -f docker-compose.staging.yml build backend

# Vérifier les images
docker images | grep real-estate
```

### Étape 2 : Démarrer les services

```bash
# Démarrer tous les services
docker compose -f docker-compose.staging.yml up -d

# Vérifier les services
docker compose -f docker-compose.staging.yml ps

# Afficher les logs
docker compose -f docker-compose.staging.yml logs -f backend
```

### Étape 3 : Initialiser la base de données

```bash
# Attendre que PostgreSQL soit prêt
sleep 10

# Créer les tables
docker compose -f docker-compose.staging.yml exec backend python3 << 'EOF'
from app.database import engine, Base
Base.metadata.create_all(bind=engine)
print("✓ Database initialized")
EOF
```

### Étape 4 : Vérifier le déploiement

```bash
# Vérifier la santé de l'API
curl http://localhost:8000/health

# Accéder à Swagger UI
curl http://localhost:8000/docs

# Vérifier les services
curl http://localhost:8000/api/info
curl http://localhost:3000  # Grafana
curl http://localhost:9090  # Prometheus
curl http://localhost:5173  # Frontend (si activé)
```

## 4. Accès aux Services

| Service | URL | Identifiants |
|---------|-----|--------------|
| **API** | http://localhost:8000 | - |
| **Swagger UI** | http://localhost:8000/docs | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Frontend** | http://localhost:5173 | - |
| **PostgreSQL** | localhost:5432 | scraper / staging_password_change_me |
| **Redis** | localhost:6379 | - |

## 5. Gestion des Services

### Arrêter les services

```bash
docker compose -f docker-compose.staging.yml down
```

### Arrêter et supprimer les volumes

```bash
docker compose -f docker-compose.staging.yml down -v
```

### Redémarrer un service

```bash
docker compose -f docker-compose.staging.yml restart backend
```

### Voir les logs

```bash
# Tous les logs
docker compose -f docker-compose.staging.yml logs

# Logs en temps réel
docker compose -f docker-compose.staging.yml logs -f

# Logs d'un service spécifique
docker compose -f docker-compose.staging.yml logs -f backend

# Dernières 100 lignes
docker compose -f docker-compose.staging.yml logs --tail=100 backend
```

## 6. Exécuter des Commandes dans les Conteneurs

### Accéder au shell du backend

```bash
docker compose -f docker-compose.staging.yml exec backend bash
```

### Exécuter une commande Python

```bash
docker compose -f docker-compose.staging.yml exec backend python3 << 'EOF'
from app.database import SessionLocal
from app.models import User

db = SessionLocal()
users = db.query(User).all()
print(f"Total users: {len(users)}")
EOF
```

### Accéder à PostgreSQL

```bash
docker compose -f docker-compose.staging.yml exec db psql -U scraper -d real_estate_scraper
```

### Accéder à Redis

```bash
docker compose -f docker-compose.staging.yml exec redis redis-cli
```

## 7. Monitoring et Logs

### Prometheus

1. Ouvrir http://localhost:9090
2. Aller à "Graph"
3. Chercher des métriques comme `requests_total`, `request_duration_seconds`

### Grafana

1. Ouvrir http://localhost:3000
2. Se connecter avec admin/admin
3. Ajouter Prometheus comme data source
4. Créer des dashboards

### Logs centralisés

```bash
# Afficher les logs du backend
docker compose -f docker-compose.staging.yml logs backend | tail -100

# Afficher les logs avec timestamps
docker compose -f docker-compose.staging.yml logs --timestamps backend

# Afficher les logs depuis une date
docker compose -f docker-compose.staging.yml logs --since 2024-02-21 backend
```

## 8. Mise à Jour du Code

### Redéployer après modifications

```bash
# Arrêter les services
docker compose -f docker-compose.staging.yml down

# Reconstruire les images
docker compose -f docker-compose.staging.yml build --no-cache backend

# Redémarrer
docker compose -f docker-compose.staging.yml up -d

# Vérifier
docker compose -f docker-compose.staging.yml logs -f backend
```

### Mise à jour des dépendances

```bash
# Modifier backend/requirements.txt

# Reconstruire
docker compose -f docker-compose.staging.yml build --no-cache backend

# Redémarrer
docker compose -f docker-compose.staging.yml up -d
```

## 9. Backups

### Backup PostgreSQL

```bash
# Backup manuel
docker compose -f docker-compose.staging.yml exec db pg_dump -U scraper real_estate_scraper > backup.sql

# Backup compressé
docker compose -f docker-compose.staging.yml exec db pg_dump -U scraper real_estate_scraper | gzip > backup_$(date +%Y%m%d).sql.gz

# Restaurer
docker compose -f docker-compose.staging.yml exec -T db psql -U scraper real_estate_scraper < backup.sql
```

### Backup des volumes

```bash
# Backup PostgreSQL volume
docker run --rm -v real-estate-scraper_postgres_data_staging:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restaurer
docker run --rm -v real-estate-scraper_postgres_data_staging:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## 10. Scaling

### Augmenter les ressources

```yaml
# Dans docker-compose.staging.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Exécuter plusieurs instances

```bash
# Utiliser un load balancer (Nginx)
docker compose -f docker-compose.staging.yml up -d --scale backend=3
```

## 11. Sécurité

### Changer les mots de passe par défaut

```bash
# Modifier .env.staging
POSTGRES_PASSWORD=your-secure-password
GRAFANA_ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-secure-secret-key
```

### Utiliser HTTPS

```yaml
# Ajouter Nginx avec SSL
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
```

### Limiter l'accès

```bash
# Firewall
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 9090/tcp
sudo ufw enable
```

## 12. Troubleshooting

### Le backend ne démarre pas

```bash
# Vérifier les logs
docker compose -f docker-compose.staging.yml logs backend

# Vérifier la santé
docker compose -f docker-compose.staging.yml ps

# Redémarrer
docker compose -f docker-compose.staging.yml restart backend
```

### PostgreSQL ne démarre pas

```bash
# Vérifier les permissions
docker compose -f docker-compose.staging.yml exec db ls -la /var/lib/postgresql/data

# Supprimer et recréer le volume
docker compose -f docker-compose.staging.yml down -v
docker compose -f docker-compose.staging.yml up -d
```

### Erreur de connexion à la base de données

```bash
# Vérifier la connexion
docker compose -f docker-compose.staging.yml exec backend python3 << 'EOF'
from app.database import engine
try:
    with engine.connect() as conn:
        print("✓ Database connection OK")
except Exception as e:
    print(f"✗ Error: {e}")
EOF
```

### Erreur de mémoire

```bash
# Vérifier l'utilisation
docker stats

# Augmenter la limite
docker compose -f docker-compose.staging.yml down
# Modifier docker-compose.staging.yml pour augmenter les ressources
docker compose -f docker-compose.staging.yml up -d
```

## 13. Nettoyage

### Supprimer les conteneurs arrêtés

```bash
docker container prune
```

### Supprimer les images inutilisées

```bash
docker image prune
```

### Supprimer les volumes inutilisés

```bash
docker volume prune
```

### Nettoyage complet

```bash
docker system prune -a
```

## 14. Ressources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)
- [Prometheus Docker Image](https://hub.docker.com/r/prom/prometheus)
- [Grafana Docker Image](https://hub.docker.com/r/grafana/grafana)
