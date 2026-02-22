# Guide de Test des Alertes en Production

Guide complet pour tester et valider les alertes Prometheus en environnement de production.

## 1. Architecture des Alertes

```
┌──────────────────┐
│  Application     │
│  (Métriques)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Prometheus      │
│  (Évalue règles) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Alertmanager    │
│  (Envoie alertes)│
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
  Email     Slack
```

## 2. Préparation

### Vérifier que Prometheus est opérationnel

```bash
# Accéder à Prometheus
curl http://localhost:9090

# Vérifier les targets
curl http://localhost:9090/api/v1/targets

# Vérifier les règles d'alerte
curl http://localhost:9090/api/v1/rules
```

### Vérifier que Alertmanager est opérationnel

```bash
# Accéder à Alertmanager
curl http://localhost:9093

# Vérifier les alertes
curl http://localhost:9093/api/v1/alerts

# Vérifier la configuration
curl http://localhost:9093/api/v1/status
```

## 3. Test 1 : Alerte d'Erreur Élevée

### Objectif
Déclencher l'alerte `HighErrorRate` en générant des erreurs.

### Étapes

1. **Générer des erreurs**

```bash
# Faire 100 requêtes avec erreur (endpoint invalide)
for i in {1..100}; do
  curl -s http://localhost:8000/api/invalid-endpoint 2>/dev/null &
done
wait
```

2. **Vérifier la métrique**

```bash
# Requête Prometheus
curl 'http://localhost:9090/api/v1/query?query=rate(requests_total{status=~"5.."}[5m])'

# Ou accéder à Prometheus UI
# http://localhost:9090/graph
# Chercher: rate(requests_total{status=~"5.."}[5m])
```

3. **Vérifier l'alerte**

```bash
# Vérifier les alertes dans Prometheus
curl http://localhost:9090/api/v1/alerts

# Vérifier les alertes dans Alertmanager
curl http://localhost:9093/api/v1/alerts

# Accéder à l'UI Alertmanager
# http://localhost:9093
```

4. **Vérifier l'email**

- Vérifier la boîte email configurée
- L'email doit arriver dans les 5 minutes

### Résultat attendu

```
✓ Alerte HighErrorRate déclenchée
✓ Email reçu avec le détail de l'alerte
✓ Alerte visible dans Prometheus et Alertmanager
```

## 4. Test 2 : Alerte de Temps de Réponse Lent

### Objectif
Déclencher l'alerte `SlowResponseTime` en ralentissant les requêtes.

### Étapes

1. **Ajouter un délai au backend**

```python
# backend/app/main.py
import time

@app.get("/api/slow-endpoint")
async def slow_endpoint():
    time.sleep(2)  # 2 secondes de délai
    return {"message": "slow response"}
```

2. **Générer des requêtes lentes**

```bash
# Faire 50 requêtes lentes
for i in {1..50}; do
  curl -s http://localhost:8000/api/slow-endpoint 2>/dev/null &
done
wait
```

3. **Vérifier la métrique**

```bash
# Requête Prometheus
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(request_duration_seconds_bucket[5m]))'
```

4. **Vérifier l'alerte**

```bash
# Vérifier dans Alertmanager
curl http://localhost:9093/api/v1/alerts
```

### Résultat attendu

```
✓ Alerte SlowResponseTime déclenchée
✓ Email reçu
✓ Temps de réponse P95 > 1s
```

## 5. Test 3 : Alerte de Scraping Échoué

### Objectif
Déclencher l'alerte `ScrapingFailed` en arrêtant le scraper.

### Étapes

1. **Arrêter le scraper**

```bash
# Modifier le code du scraper pour ne rien scraper
# Ou arrêter le service de scraping
```

2. **Attendre 1 heure**

```bash
# L'alerte se déclenche après 1 heure sans scraping
# Pour tester plus vite, modifier la règle:
# for: 1h  →  for: 5m
```

3. **Vérifier l'alerte**

```bash
# Vérifier dans Alertmanager
curl http://localhost:9093/api/v1/alerts
```

### Résultat attendu

```
✓ Alerte ScrapingFailed déclenchée
✓ Email reçu
```

## 6. Test 4 : Alerte d'Utilisation Mémoire Élevée

### Objectif
Déclencher l'alerte `HighMemoryUsage` en consommant de la mémoire.

### Étapes

1. **Consommer de la mémoire**

```python
# backend/app/main.py
@app.get("/api/memory-leak")
async def memory_leak():
    # Créer une grande liste en mémoire
    big_list = [i for i in range(100000000)]
    return {"status": "ok"}
```

2. **Générer des requêtes**

```bash
# Faire plusieurs requêtes
for i in {1..5}; do
  curl -s http://localhost:8000/api/memory-leak 2>/dev/null &
done
wait
```

3. **Vérifier la métrique**

```bash
# Requête Prometheus
curl 'http://localhost:9090/api/v1/query?query=process_resident_memory_bytes'
```

4. **Vérifier l'alerte**

```bash
# Vérifier dans Alertmanager
curl http://localhost:9093/api/v1/alerts
```

### Résultat attendu

```
✓ Alerte HighMemoryUsage déclenchée
✓ Email reçu
✓ Mémoire utilisée > 1GB
```

## 7. Test 5 : Alerte d'Application Indisponible

### Objectif
Déclencher l'alerte `ApplicationDown` en arrêtant l'application.

### Étapes

1. **Arrêter l'application**

```bash
# Arrêter le backend
docker compose -f docker-compose.staging.yml stop backend

# Ou tuer le processus
lsof -i :8000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9
```

2. **Attendre 1 minute**

```bash
# L'alerte se déclenche après 1 minute sans réponse
sleep 60
```

3. **Vérifier l'alerte**

```bash
# Vérifier dans Alertmanager
curl http://localhost:9093/api/v1/alerts

# Vérifier dans Prometheus
curl http://localhost:9090/api/v1/alerts
```

4. **Redémarrer l'application**

```bash
# Redémarrer le backend
docker compose -f docker-compose.staging.yml start backend
```

### Résultat attendu

```
✓ Alerte ApplicationDown déclenchée
✓ Email reçu
✓ Alerte résolue après redémarrage
```

## 8. Test 6 : Alerte de Connexions DB Élevées

### Objectif
Déclencher l'alerte `HighDatabaseConnections` en créant beaucoup de connexions.

### Étapes

1. **Générer beaucoup de requêtes**

```bash
# Faire 100 requêtes parallèles
for i in {1..100}; do
  curl -s http://localhost:8000/api/listings/?postal_code=75015 2>/dev/null &
done
wait
```

2. **Vérifier la métrique**

```bash
# Requête Prometheus
curl 'http://localhost:9090/api/v1/query?query=database_connections'
```

3. **Vérifier l'alerte**

```bash
# Vérifier dans Alertmanager
curl http://localhost:9093/api/v1/alerts
```

### Résultat attendu

```
✓ Alerte HighDatabaseConnections déclenchée
✓ Email reçu
```

## 9. Validation des Alertes

### Checklist de validation

```bash
# 1. Vérifier que Prometheus scrape les métriques
curl http://localhost:9090/api/v1/targets | grep -i "state.*up"

# 2. Vérifier que les règles sont chargées
curl http://localhost:9090/api/v1/rules | grep -i "real_estate"

# 3. Vérifier que Alertmanager reçoit les alertes
curl http://localhost:9093/api/v1/alerts | jq '.data | length'

# 4. Vérifier que les emails sont envoyés
# Vérifier la boîte email

# 5. Vérifier que les alertes se résolvent
# Arrêter les actions qui causent l'alerte
# Vérifier que l'alerte est résolue après quelques minutes
```

## 10. Configuration des Notifications

### Email

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
  smtp_from: 'alerts@real-estate-scraper.com'

receivers:
  - name: 'email'
    email_configs:
      - to: 'admin@real-estate-scraper.com'
```

### Slack

```yaml
# alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
```

### PagerDuty

```yaml
# alertmanager.yml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}'
```

## 11. Monitoring des Alertes

### Métriques Alertmanager

```bash
# Nombre d'alertes
curl 'http://localhost:9090/api/v1/query?query=alertmanager_alerts'

# Alertes par sévérité
curl 'http://localhost:9090/api/v1/query?query=alertmanager_alerts{severity="critical"}'

# Alertes résolues
curl 'http://localhost:9090/api/v1/query?query=alertmanager_alerts{state="resolved"}'
```

### Dashboard Grafana

Créer un dashboard pour visualiser :
- Nombre d'alertes actives
- Alertes par sévérité
- Historique des alertes
- Temps de résolution moyen

## 12. Troubleshooting

### Les alertes ne se déclenchent pas

```bash
# 1. Vérifier que Prometheus scrape les métriques
curl http://localhost:9090/api/v1/targets

# 2. Vérifier que les règles sont correctes
curl http://localhost:9090/api/v1/rules

# 3. Vérifier les logs Prometheus
docker compose -f docker-compose.staging.yml logs prometheus

# 4. Tester manuellement
curl 'http://localhost:9090/api/v1/query?query=requests_total'
```

### Les emails ne s'envoient pas

```bash
# 1. Vérifier la configuration SMTP
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-password')
print('✓ SMTP OK')
"

# 2. Vérifier les logs Alertmanager
docker compose -f docker-compose.staging.yml logs alertmanager

# 3. Vérifier que les alertes arrivent à Alertmanager
curl http://localhost:9093/api/v1/alerts
```

### Les alertes ne se résolvent pas

```bash
# 1. Vérifier que la condition d'alerte n'est plus vraie
curl 'http://localhost:9090/api/v1/query?query=<alert_condition>'

# 2. Attendre le délai de résolution
# Par défaut: 5 minutes

# 3. Vérifier les logs
docker compose -f docker-compose.staging.yml logs prometheus
```

## 13. Ressources

- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Alert Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Notification Templates](https://prometheus.io/docs/alerting/latest/notification_template_reference/)
