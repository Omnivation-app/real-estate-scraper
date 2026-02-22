# Configuration du Monitoring avec Prometheus et Grafana

Guide complet pour mettre en place le monitoring de l'application avec Prometheus et Grafana.

## 1. Architecture du Monitoring

```
┌─────────────────┐
│  Application    │
│  (FastAPI)      │
│  /metrics       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Prometheus     │ (Scrape metrics toutes les 15s)
│  :9090          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Grafana        │ (Visualisation)
│  :3000          │
└─────────────────┘
```

## 2. Installation Prometheus

### Étape 1 : Télécharger Prometheus

```bash
# Télécharger la dernière version
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz

# Extraire
tar xvfz prometheus-2.40.0.linux-amd64.tar.gz
cd prometheus-2.40.0.linux-amd64
```

### Étape 2 : Configurer Prometheus

Créer `prometheus.yml` :

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'real-estate-scraper'

scrape_configs:
  - job_name: 'real-estate-scraper'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 15s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
    scrape_interval: 15s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
    scrape_interval: 15s
```

### Étape 3 : Démarrer Prometheus

```bash
# Démarrer le serveur
./prometheus --config.file=prometheus.yml

# Vérifier
curl http://localhost:9090
```

## 3. Installation Grafana

### Étape 1 : Installer Grafana

```bash
# Sur Ubuntu/Debian
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana-server

# Démarrer le service
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Vérifier
curl http://localhost:3000
```

### Étape 2 : Accéder à Grafana

1. Ouvrir http://localhost:3000
2. Se connecter avec admin/admin
3. Changer le mot de passe

### Étape 3 : Ajouter Prometheus comme Data Source

1. Aller à Configuration → Data Sources
2. Cliquer sur "Add data source"
3. Sélectionner "Prometheus"
4. URL: http://localhost:9090
5. Cliquer sur "Save & Test"

## 4. Métriques de l'Application

### Ajouter Prometheus au Backend

Installer la dépendance :

```bash
pip install prometheus-client
```

Créer `backend/app/metrics.py` :

```python
from prometheus_client import Counter, Histogram, Gauge
import time

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

errors_total = Counter(
    'errors_total',
    'Total errors',
    ['type', 'endpoint']
)

# Histograms
request_duration_seconds = Histogram(
    'request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

scraping_duration_seconds = Histogram(
    'scraping_duration_seconds',
    'Scraping duration',
    ['source']
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

cache_hits = Gauge(
    'cache_hits_total',
    'Total cache hits'
)

cache_misses = Gauge(
    'cache_misses_total',
    'Total cache misses'
)
```

### Intégrer les Métriques

Ajouter à `backend/app/main.py` :

```python
from prometheus_client import make_asgi_app, REGISTRY
from app.metrics import (
    requests_total, request_duration_seconds,
    active_requests, errors_total
)
import time

# Ajouter l'endpoint /metrics
metrics_app = make_asgi_app()

app.mount("/metrics", metrics_app)

# Middleware pour tracker les requêtes
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()
    active_requests.inc()
    
    try:
        response = await call_next(request)
        
        # Enregistrer les métriques
        duration = time.time() - start_time
        requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    
    except Exception as e:
        errors_total.labels(
            type=type(e).__name__,
            endpoint=request.url.path
        ).inc()
        raise
    
    finally:
        active_requests.dec()
```

## 5. Créer des Dashboards Grafana

### Dashboard 1 : Vue d'ensemble

1. Créer un nouveau dashboard
2. Ajouter les panneaux suivants :

**Requêtes par seconde**
```
rate(requests_total[1m])
```

**Temps de réponse moyen**
```
rate(request_duration_seconds_sum[5m]) / rate(request_duration_seconds_count[5m])
```

**Taux d'erreur**
```
rate(errors_total[5m])
```

**Connexions actives**
```
active_requests
```

### Dashboard 2 : Scraping

**Annonces scrapées par source**
```
increase(listings_scraped_total[1h])
```

**Durée de scraping**
```
scraping_duration_seconds_bucket
```

**Taux de succès de scraping**
```
(listings_scraped_total - errors_total) / listings_scraped_total
```

### Dashboard 3 : Base de données

**Connexions actives**
```
database_connections
```

**Requêtes lentes**
```
histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))
```

**Utilisation du cache**
```
cache_hits / (cache_hits + cache_misses)
```

### Dashboard 4 : Système

**Utilisation CPU**
```
rate(process_cpu_seconds_total[5m])
```

**Mémoire utilisée**
```
process_resident_memory_bytes
```

**Uptime**
```
time() - process_start_time_seconds
```

## 6. Alertes Prometheus

Créer `alerts.yml` :

```yaml
groups:
  - name: real_estate_scraper
    interval: 30s
    rules:
      # Alerte : Taux d'erreur élevé
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Taux d'erreur élevé"
          description: "Le taux d'erreur est {{ $value | humanizePercentage }}"

      # Alerte : Temps de réponse lent
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Temps de réponse lent"
          description: "Le temps de réponse P95 est {{ $value | humanizeDuration }}"

      # Alerte : Scraping échoué
      - alert: ScrapingFailed
        expr: rate(listings_scraped_total[1h]) == 0
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Scraping échoué"
          description: "Aucune annonce n'a été scrapée dans la dernière heure"

      # Alerte : Utilisation mémoire élevée
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes > 1000000000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Utilisation mémoire élevée"
          description: "Mémoire utilisée : {{ $value | humanize }}B"

      # Alerte : Application down
      - alert: ApplicationDown
        expr: up{job="real-estate-scraper"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Application indisponible"
          description: "L'application n'a pas répondu aux dernières 1 minute"
```

Ajouter à `prometheus.yml` :

```yaml
rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093
```

## 7. Alertes Email

Créer `alertmanager.yml` :

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
  smtp_from: 'alerts@real-estate-scraper.com'

route:
  receiver: 'email'
  group_by: ['alertname', 'cluster']
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

## 8. Exporters Supplémentaires

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

## 9. Logs Centralisés (ELK Stack)

### Installation

```bash
# Elasticsearch
docker run -d \
  --name elasticsearch \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -p 9200:9200 \
  docker.elastic.co/elasticsearch/elasticsearch:8.0.0

# Logstash
docker run -d \
  --name logstash \
  -v /etc/logstash/logstash.conf:/usr/share/logstash/pipeline/logstash.conf \
  -p 5000:5000 \
  docker.elastic.co/logstash/logstash:8.0.0

# Kibana
docker run -d \
  --name kibana \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" \
  -p 5601:5601 \
  docker.elastic.co/kibana/kibana:8.0.0
```

### Configuration Logstash

Créer `/etc/logstash/logstash.conf` :

```
input {
  file {
    path => "/var/log/real-estate-scraper.log"
    start_position => "beginning"
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "real-estate-scraper-%{+YYYY.MM.dd}"
  }
}
```

## 10. Dashboards JSON

Exporter les dashboards :

```bash
# Récupérer l'ID du dashboard
curl http://localhost:3000/api/search?query=dashboard

# Exporter
curl http://localhost:3000/api/dashboards/uid/DASHBOARD_UID > dashboard.json
```

Importer les dashboards :

```bash
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @dashboard.json
```

## 11. Troubleshooting

### Prometheus ne scrape pas les métriques

```bash
# Vérifier la configuration
curl http://localhost:9090/api/v1/query?query=up

# Vérifier les targets
curl http://localhost:9090/api/v1/targets

# Vérifier les logs
tail -f /var/log/prometheus.log
```

### Grafana ne se connecte pas à Prometheus

```bash
# Vérifier la connexion
curl http://localhost:9090

# Vérifier les logs Grafana
sudo journalctl -u grafana-server -f

# Vérifier la configuration
curl http://localhost:3000/api/datasources
```

### Alertes ne s'envoient pas

```bash
# Vérifier Alertmanager
curl http://localhost:9093/api/v1/alerts

# Vérifier les logs Alertmanager
tail -f /var/log/alertmanager.log

# Tester la connexion SMTP
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print('✓ SMTP connection successful')
"
```

## 12. Ressources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Node Exporter](https://github.com/prometheus/node_exporter)
- [PostgreSQL Exporter](https://github.com/prometheuscommunity/postgres_exporter)
- [Redis Exporter](https://github.com/oliver006/redis_exporter)
- [ELK Stack](https://www.elastic.co/what-is/elk-stack)
