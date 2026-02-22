# Guide Complet du Monitoring — Prometheus + Grafana

Configuration complète du monitoring pour l'application Real Estate Scraper.

## 1. Architecture du Monitoring

```
┌─────────────────────────────────────────────────────────┐
│                   Application                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastAPI Backend                                  │   │
│  │  - /metrics endpoint (Prometheus format)         │   │
│  │  - Request metrics                               │   │
│  │  - Scraping metrics                              │   │
│  │  - Database metrics                              │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │ (scrape every 15s)
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Prometheus (Port 9090)                                 │
│  - Collecte les métriques                               │
│  - Évalue les règles d'alerte                           │
│  - Stockage TSDB (15 jours par défaut)                  │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   ┌─────────┐      ┌──────────────┐
   │ Grafana │      │ Alertmanager │
   │ (3000)  │      │ (9093)       │
   └─────────┘      └──────┬───────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                  Email         Slack
```

## 2. Installation Prometheus

### Avec Docker Compose (Recommandé)

```bash
# Déjà inclus dans docker-compose.staging.yml
docker compose -f docker-compose.staging.yml up -d prometheus
```

### Installation manuelle

```bash
# Télécharger
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz

# Extraire
tar xvfz prometheus-2.40.0.linux-amd64.tar.gz
cd prometheus-2.40.0.linux-amd64

# Démarrer
./prometheus --config.file=prometheus.yml
```

## 3. Configuration Prometheus

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'real-estate-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Vérifier la configuration

```bash
# Accéder à Prometheus
curl http://localhost:9090

# Vérifier les targets
curl http://localhost:9090/api/v1/targets

# Exécuter une requête
curl 'http://localhost:9090/api/v1/query?query=up'
```

## 4. Installation Grafana

### Avec Docker Compose

```bash
docker compose -f docker-compose.staging.yml up -d grafana
```

### Installation manuelle

```bash
# Ubuntu/Debian
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana-server

# Démarrer
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

## 5. Configuration Grafana

### Accès initial

1. Ouvrir http://localhost:3000
2. Se connecter : admin / admin
3. Changer le mot de passe

### Ajouter Prometheus comme Data Source

1. Aller à Configuration → Data Sources
2. Cliquer "Add data source"
3. Sélectionner "Prometheus"
4. URL: http://prometheus:9090 (ou http://localhost:9090)
5. Cliquer "Save & Test"

## 6. Créer des Dashboards

### Dashboard 1 : Vue d'ensemble API

**Panneau 1 : Requêtes par seconde**
```
rate(requests_total[1m])
```

**Panneau 2 : Temps de réponse moyen**
```
rate(request_duration_seconds_sum[5m]) / rate(request_duration_seconds_count[5m])
```

**Panneau 3 : Taux d'erreur**
```
rate(requests_total{status=~"5.."}[5m]) / rate(requests_total[5m])
```

**Panneau 4 : Requêtes actives**
```
active_requests
```

### Dashboard 2 : Scraping

**Panneau 1 : Annonces scrapées par source**
```
increase(listings_scraped_total[1h])
```

**Panneau 2 : Durée moyenne de scraping**
```
rate(scraping_duration_seconds_sum[5m]) / rate(scraping_duration_seconds_count[5m])
```

**Panneau 3 : Taux de succès**
```
(listings_scraped_total - errors_total) / listings_scraped_total
```

### Dashboard 3 : Base de données

**Panneau 1 : Connexions actives**
```
database_connections
```

**Panneau 2 : Durée des requêtes (P95)**
```
histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))
```

**Panneau 3 : Taux de hit du cache**
```
cache_hits / (cache_hits + cache_misses)
```

### Dashboard 4 : Système

**Panneau 1 : Utilisation CPU**
```
rate(process_cpu_seconds_total[5m])
```

**Panneau 2 : Mémoire utilisée**
```
process_resident_memory_bytes / 1024 / 1024 / 1024
```

**Panneau 3 : Uptime**
```
(time() - process_start_time_seconds) / 3600 / 24
```

## 7. Configuration des Alertes

### Fichier alerts.yml

```yaml
groups:
  - name: real_estate_scraper
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Taux d'erreur élevé"
          description: "Le taux d'erreur est {{ $value | humanizePercentage }}"
```

### Ajouter les règles à Prometheus

```yaml
# prometheus.yml
rule_files:
  - 'alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'localhost:9093'
```

## 8. Installation Alertmanager

### Télécharger

```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz

tar xvfz alertmanager-0.25.0.linux-amd64.tar.gz
cd alertmanager-0.25.0.linux-amd64
```

### Configuration alertmanager.yml

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
  smtp_from: 'alerts@real-estate-scraper.com'

route:
  receiver: 'email'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'email'
    email_configs:
      - to: 'admin@real-estate-scraper.com'
        headers:
          Subject: '[{{ .GroupLabels.alertname }}] {{ .Status }}'
```

### Démarrer Alertmanager

```bash
./alertmanager --config.file=alertmanager.yml
```

## 9. Métriques Personnalisées

### Ajouter des métriques au backend

```python
# backend/app/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Counters
requests_total = Counter(
    'requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

listings_scraped_total = Counter(
    'listings_scraped_total',
    'Total listings scraped',
    ['source']
)

# Histograms
request_duration_seconds = Histogram(
    'request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Gauges
active_requests = Gauge(
    'active_requests',
    'Active HTTP requests'
)

database_connections = Gauge(
    'database_connections',
    'Active database connections'
)
```

### Utiliser les métriques

```python
# backend/app/main.py
from prometheus_client import make_asgi_app
from app.metrics import requests_total, active_requests

# Ajouter l'endpoint /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middleware pour tracker les requêtes
@app.middleware("http")
async def track_requests(request: Request, call_next):
    active_requests.inc()
    try:
        response = await call_next(request)
        requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        return response
    finally:
        active_requests.dec()
```

## 10. Exporters Supplémentaires

### Node Exporter (Système)

```bash
# Télécharger
wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz

# Extraire et démarrer
tar xvfz node_exporter-1.5.0.linux-amd64.tar.gz
./node_exporter-1.5.0.linux-amd64/node_exporter
```

### PostgreSQL Exporter

```bash
# Docker
docker run -d \
  --name postgres_exporter \
  -e DATA_SOURCE_NAME="postgresql://scraper:password@localhost:5432/real_estate_scraper?sslmode=disable" \
  -p 9187:9187 \
  prometheuscommunity/postgres-exporter
```

### Redis Exporter

```bash
# Docker
docker run -d \
  --name redis_exporter \
  -p 9121:9121 \
  oliver006/redis_exporter \
  -redis-addr=localhost:6379
```

## 11. Requêtes Prometheus Utiles

### Santé générale

```
# Uptime
time() - process_start_time_seconds

# Taux d'erreur
rate(errors_total[5m])

# Requêtes par seconde
rate(requests_total[1m])
```

### Performance

```
# Temps de réponse P50
histogram_quantile(0.50, rate(request_duration_seconds_bucket[5m]))

# Temps de réponse P95
histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))

# Temps de réponse P99
histogram_quantile(0.99, rate(request_duration_seconds_bucket[5m]))
```

### Scraping

```
# Annonces scrapées par heure
increase(listings_scraped_total[1h])

# Taux de succès
(listings_scraped_total - errors_total) / listings_scraped_total

# Durée moyenne
rate(scraping_duration_seconds_sum[5m]) / rate(scraping_duration_seconds_count[5m])
```

## 12. Troubleshooting

### Prometheus ne scrape pas

```bash
# Vérifier les targets
curl http://localhost:9090/api/v1/targets

# Vérifier la configuration
curl http://localhost:9090/api/v1/status/config

# Vérifier les logs
tail -f /var/log/prometheus.log
```

### Grafana ne se connecte pas à Prometheus

```bash
# Vérifier la connexion
curl http://localhost:9090

# Vérifier les logs Grafana
sudo journalctl -u grafana-server -f

# Tester manuellement
curl http://prometheus:9090/api/v1/query?query=up
```

### Alertes ne s'envoient pas

```bash
# Vérifier Alertmanager
curl http://localhost:9093/api/v1/alerts

# Vérifier les logs
tail -f /var/log/alertmanager.log

# Tester SMTP
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-password')
print('✓ SMTP OK')
"
```

## 13. Ressources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Prometheus Querying](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Library](https://grafana.com/grafana/dashboards/)
