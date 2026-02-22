# Guide Complet de Monitoring et Alertes — Production

## 🎯 Objectif

Mettre en place un système de monitoring complet pour surveiller la santé de l'application, les performances du scraping, et les anomalies en temps réel.

---

## 📊 Métriques à Surveiller

### 1. **Santé de l'Application**

| Métrique | Seuil d'Alerte | Vérification |
|----------|----------------|-------------|
| Uptime API | < 99.9% | Toutes les minutes |
| Temps réponse P95 | > 1s | Toutes les 5 min |
| Taux d'erreur HTTP | > 5% | Toutes les 5 min |
| Connexion BD | Échouée | Toutes les 30s |
| Connexion Redis | Échouée | Toutes les 30s |
| Espace disque | > 90% | Toutes les heures |
| Mémoire | > 85% | Toutes les minutes |
| CPU | > 80% | Toutes les minutes |

### 2. **Scraping**

| Métrique | Seuil d'Alerte | Vérification |
|----------|----------------|-------------|
| Agences bloquées | > 10% | Toutes les heures |
| Taux d'erreur scraping | > 20% | Toutes les heures |
| Annonces trouvées/h | < 100 | Toutes les heures |
| Temps moyen scraping | > 5min | Toutes les heures |
| Agences non scrapées > 48h | > 5% | Toutes les 6h |

### 3. **Base de Données**

| Métrique | Seuil d'Alerte | Vérification |
|----------|----------------|-------------|
| Requêtes lentes (> 1s) | > 10/min | Toutes les minutes |
| Connexions actives | > 80% du max | Toutes les 5 min |
| Taille BD | > 90% du disque | Toutes les heures |
| Deadlocks | > 0 | En temps réel |
| Réplication lag | > 10s | Toutes les 30s |

### 4. **Utilisateurs**

| Métrique | Seuil d'Alerte | Vérification |
|----------|----------------|-------------|
| Utilisateurs actifs | < 10 | Toutes les heures |
| Erreurs de login | > 20% | Toutes les 5 min |
| Alertes non envoyées | > 10 | Toutes les heures |
| Favoris perdus | > 0 | En temps réel |

---

## 🔧 Configuration Prometheus

### Installation

```bash
# Télécharger Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-2.40.0.linux-amd64.tar.gz
cd prometheus-2.40.0.linux-amd64
```

### Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'real-estate-scraper'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

rule_files:
  - 'alerts.yml'

scrape_configs:
  # API FastAPI
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  # PostgreSQL
  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:5432']

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']

  # Node Exporter (système)
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  # Celery
  - job_name: 'celery'
    static_configs:
      - targets: ['localhost:5555']
```

### Démarrer Prometheus

```bash
./prometheus --config.file=prometheus.yml --storage.tsdb.path=data/
```

Accès : http://localhost:9090

---

## 🚨 Configuration des Alertes

### Fichier `alerts.yml`

```yaml
groups:
  - name: real_estate_scraper
    interval: 30s
    rules:
      # === API ===
      - alert: APIDown
        expr: up{job="fastapi"} == 0
        for: 1m
        annotations:
          summary: "API FastAPI est down"
          description: "L'API n'est pas accessible depuis {{ $value }} minutes"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Taux d'erreur élevé ({{ $value | humanizePercentage }})"
          description: "Plus de 5% des requêtes retournent une erreur 5xx"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1
        for: 5m
        annotations:
          summary: "Temps de réponse lent ({{ $value | humanizeDuration }})"
          description: "Le P95 du temps de réponse dépasse 1 seconde"

      # === Base de Données ===
      - alert: DatabaseDown
        expr: up{job="postgresql"} == 0
        for: 1m
        annotations:
          summary: "PostgreSQL est down"
          description: "La base de données n'est pas accessible"

      - alert: SlowQueries
        expr: rate(pg_slow_queries_total[5m]) > 10
        for: 5m
        annotations:
          summary: "Trop de requêtes lentes ({{ $value | humanize }})"
          description: "Plus de 10 requêtes lentes par minute"

      - alert: HighConnectionCount
        expr: pg_stat_activity_count > 80
        for: 5m
        annotations:
          summary: "Trop de connexions BD ({{ $value }})"
          description: "Plus de 80 connexions actives"

      # === Redis ===
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        annotations:
          summary: "Redis est down"
          description: "Redis n'est pas accessible"

      - alert: HighRedisMemory
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        annotations:
          summary: "Mémoire Redis élevée ({{ $value | humanizePercentage }})"
          description: "Redis utilise plus de 90% de sa mémoire"

      # === Scraping ===
      - alert: ScrapingFailureRate
        expr: rate(scraping_failures_total[1h]) > 0.2
        for: 1h
        annotations:
          summary: "Taux d'échec scraping élevé ({{ $value | humanizePercentage }})"
          description: "Plus de 20% des scrapings échouent"

      - alert: AgenciesBlocked
        expr: count(agency_scraping_status{status="blocked"}) > 10
        for: 1h
        annotations:
          summary: "{{ $value }} agences bloquées"
          description: "Trop d'agences sont bloquées (IP bannie ?)"

      - alert: NoListingsFound
        expr: rate(listings_found_total[1h]) < 100
        for: 1h
        annotations:
          summary: "Peu d'annonces trouvées ({{ $value | humanize }}/h)"
          description: "Moins de 100 annonces trouvées par heure"

      - alert: AgenciesNotScraped
        expr: count(agency_last_scraped_seconds_ago > 172800) / count(agency_total) > 0.05
        for: 6h
        annotations:
          summary: "{{ $value | humanizePercentage }} d'agences non scrapées > 48h"
          description: "Trop d'agences n'ont pas été scrapées récemment"

      # === Système ===
      - alert: HighDiskUsage
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1
        for: 1h
        annotations:
          summary: "Espace disque faible ({{ $value | humanizePercentage }})"
          description: "Moins de 10% d'espace disque disponible"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.85
        for: 5m
        annotations:
          summary: "Mémoire élevée ({{ $value | humanizePercentage }})"
          description: "Plus de 85% de la mémoire est utilisée"

      - alert: HighCPUUsage
        expr: rate(node_cpu_seconds_total{mode="idle"}[5m]) < 0.2
        for: 5m
        annotations:
          summary: "CPU élevé ({{ $value | humanizePercentage }})"
          description: "Plus de 80% du CPU est utilisé"
```

---

## 📧 Configuration AlertManager

### Installation

```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.25.0.linux-amd64.tar.gz
cd alertmanager-0.25.0.linux-amd64
```

### Configuration (`alertmanager.yml`)

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      repeat_interval: 5m

    - match:
        severity: warning
      receiver: 'warning'
      repeat_interval: 1h

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true

  - name: 'critical'
    slack_configs:
      - channel: '#critical-alerts'
        title: '🚨 CRITIQUE: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ .GroupLabels.alertname }}'

  - name: 'warning'
    slack_configs:
      - channel: '#warnings'
        title: '⚠️ ATTENTION: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
```

### Démarrer AlertManager

```bash
./alertmanager --config.file=alertmanager.yml
```

Accès : http://localhost:9093

---

## 📊 Grafana Dashboards

### Installation

```bash
docker run -d -p 3000:3000 --name grafana grafana/grafana
```

Accès : http://localhost:3000 (admin/admin)

### Dashboards à Créer

#### 1. **Dashboard Général**

```json
{
  "dashboard": {
    "title": "Real Estate Scraper - Overview",
    "panels": [
      {
        "title": "API Uptime",
        "targets": [
          {
            "expr": "up{job=\"fastapi\"}"
          }
        ]
      },
      {
        "title": "Requêtes/sec",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])"
          }
        ]
      },
      {
        "title": "Taux d'erreur",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      },
      {
        "title": "Temps réponse P95",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

#### 2. **Dashboard Scraping**

```json
{
  "dashboard": {
    "title": "Real Estate Scraper - Scraping",
    "panels": [
      {
        "title": "Agences scrapées/heure",
        "targets": [
          {
            "expr": "rate(scraping_completed_total[1h])"
          }
        ]
      },
      {
        "title": "Annonces trouvées/heure",
        "targets": [
          {
            "expr": "rate(listings_found_total[1h])"
          }
        ]
      },
      {
        "title": "Taux d'erreur scraping",
        "targets": [
          {
            "expr": "rate(scraping_failures_total[1h]) / rate(scraping_total[1h])"
          }
        ]
      },
      {
        "title": "Agences par statut",
        "targets": [
          {
            "expr": "count by (status) (agency_scraping_status)"
          }
        ]
      }
    ]
  }
}
```

#### 3. **Dashboard Infrastructure**

```json
{
  "dashboard": {
    "title": "Real Estate Scraper - Infrastructure",
    "panels": [
      {
        "title": "CPU",
        "targets": [
          {
            "expr": "1 - rate(node_cpu_seconds_total{mode=\"idle\"}[5m])"
          }
        ]
      },
      {
        "title": "Mémoire",
        "targets": [
          {
            "expr": "1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)"
          }
        ]
      },
      {
        "title": "Disque",
        "targets": [
          {
            "expr": "1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)"
          }
        ]
      },
      {
        "title": "Connexions BD",
        "targets": [
          {
            "expr": "pg_stat_activity_count"
          }
        ]
      }
    ]
  }
}
```

---

## 🔔 Canaux de Notification

### Slack

```bash
# 1. Créer un webhook Slack
# https://api.slack.com/messaging/webhooks

# 2. Ajouter à alertmanager.yml
slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

### Email

```yaml
# Dans alertmanager.yml
email_configs:
  - to: 'alerts@example.com'
    from: 'alertmanager@example.com'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'your-email@gmail.com'
    auth_password: 'your-password'
    headers:
      Subject: '{{ .GroupLabels.alertname }}'
```

### PagerDuty

```yaml
# Dans alertmanager.yml
pagerduty_configs:
  - service_key: 'YOUR_SERVICE_KEY'
    description: '{{ .GroupLabels.alertname }}'
```

### Webhook Personnalisé

```yaml
# Dans alertmanager.yml
webhook_configs:
  - url: 'http://localhost:5000/alerts'
    send_resolved: true
```

---

## 📈 Métriques Personnalisées

### Ajouter des métriques à FastAPI

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Compteurs
scraping_completed = Counter('scraping_completed_total', 'Scraping complétés')
scraping_failures = Counter('scraping_failures_total', 'Scraping échoués')
listings_found = Counter('listings_found_total', 'Annonces trouvées')

# Histogrammes
scraping_duration = Histogram('scraping_duration_seconds', 'Durée du scraping')

# Jauges
agencies_blocked = Gauge('agencies_blocked', 'Agences bloquées')
active_scraping = Gauge('active_scraping', 'Scrapings actifs')

# Utilisation
@app.post("/api/discovery/scrape-agency/{agency_id}")
async def scrape_agency(agency_id: int):
    active_scraping.inc()
    start = time.time()
    
    try:
        # Scraping...
        scraping_completed.inc()
    except Exception as e:
        scraping_failures.inc()
    finally:
        scraping_duration.observe(time.time() - start)
        active_scraping.dec()
```

---

## 🧪 Tests d'Alertes

### Tester une alerte

```bash
# Arrêter l'API
docker stop fastapi

# Vérifier que l'alerte se déclenche
# http://localhost:9090/alerts

# Redémarrer l'API
docker start fastapi
```

### Simuler une charge

```bash
# Utiliser Apache Bench
ab -n 10000 -c 100 http://localhost:8000/api/listings

# Vérifier les alertes de performance
```

---

## 📋 Checklist Monitoring

- [ ] Prometheus installé et configuré
- [ ] AlertManager installé et configuré
- [ ] Alertes définies dans `alerts.yml`
- [ ] Canaux de notification configurés (Slack, Email, etc.)
- [ ] Grafana installé et dashboards créés
- [ ] Métriques personnalisées ajoutées à l'API
- [ ] Tests d'alertes effectués
- [ ] Runbooks créés pour chaque alerte
- [ ] Escalade configurée (PagerDuty)
- [ ] Logs centralisés (ELK Stack)
- [ ] Sauvegardes Prometheus configurées
- [ ] Rétention des données définie

---

## 🚀 Déploiement Complet

### Docker Compose

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"

volumes:
  prometheus_data:
  alertmanager_data:
  grafana_data:
```

### Démarrer

```bash
docker compose up -d
```

---

## 📞 Support

Pour toute question ou problème de monitoring, consultez :
- Documentation Prometheus : https://prometheus.io/docs/
- Documentation AlertManager : https://prometheus.io/docs/alerting/latest/alertmanager/
- Documentation Grafana : https://grafana.com/docs/
