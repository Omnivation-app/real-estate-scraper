# Configuration des Notifications Email/SMS

Guide complet pour configurer les notifications par email et SMS.

## 1. Configuration Email (Gmail)

### Étape 1 : Générer un mot de passe d'application

1. Accédez à [Google Account Security](https://myaccount.google.com/security)
2. Activez l'authentification à deux facteurs si ce n'est pas fait
3. Allez à "Mots de passe d'application"
4. Sélectionnez "Mail" et "Windows Computer" (ou votre appareil)
5. Générez le mot de passe (16 caractères)
6. Copiez le mot de passe généré

### Étape 2 : Configurer les variables d'environnement

Ajoutez à `backend/.env` :

```env
# Email Configuration (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
```

### Étape 3 : Tester la connexion

```bash
cd backend
python3 -c "
import smtplib
from email.mime.text import MIMEText

smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_user = 'your-email@gmail.com'
smtp_password = 'your-16-char-app-password'

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_password)
    print('✓ SMTP connection successful!')
    server.quit()
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## 2. Configuration SMS (Twilio)

### Étape 1 : Créer un compte Twilio

1. Accédez à [Twilio Console](https://www.twilio.com/console)
2. Créez un compte gratuit
3. Vérifiez votre numéro de téléphone
4. Achetez un numéro Twilio

### Étape 2 : Obtenir les credentials

1. Allez à "Account" → "API Keys & tokens"
2. Copiez votre "Account SID"
3. Copiez votre "Auth Token"
4. Notez votre numéro Twilio (ex: +1234567890)

### Étape 3 : Configurer les variables d'environnement

Ajoutez à `backend/.env` :

```env
# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Étape 4 : Tester la connexion

```bash
cd backend
python3 -c "
from twilio.rest import Client

account_sid = 'your_account_sid'
auth_token = 'your_auth_token'

try:
    client = Client(account_sid, auth_token)
    print('✓ Twilio connection successful!')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## 3. Intégration dans l'Application

### Envoyer une notification email

```python
from app.notifications import notification_service
from app.models import User, SearchAlert, Listing

# Récupérer l'utilisateur et ses alertes
user = db.query(User).filter(User.id == 1).first()
alert = db.query(SearchAlert).filter(SearchAlert.id == 1).first()

# Récupérer les nouvelles annonces
listings = db.query(Listing).filter(
    Listing.postal_code == alert.postal_code,
    Listing.price.between(alert.min_price, alert.max_price)
).all()

# Envoyer la notification
notification_service.notify_new_listings(
    user=user,
    alert=alert,
    listings=listings,
    use_email=True,
    use_sms=False
)
```

### Envoyer une notification SMS

```python
from app.notifications import notification_service

notification_service.sms_notifier.send_new_listings_notification(
    phone_number="+33612345678",
    alert_name="Appartements Paris 75015",
    listings_count=3
)
```

## 4. Automatiser les Notifications

### Option 1 : Celery + Redis

```bash
# Installer les dépendances
pip install celery redis

# Démarrer Redis
redis-server

# Démarrer Celery
celery -A app.tasks worker --loglevel=info
```

Créer `backend/app/tasks.py` :

```python
from celery import Celery
from app.notifications import notification_service
from app.database import SessionLocal
from app.models import User, SearchAlert, Listing

celery_app = Celery('real_estate_scraper')

@celery_app.task
def send_alert_notifications():
    """Envoyer les notifications pour toutes les alertes actives."""
    db = SessionLocal()
    
    try:
        alerts = db.query(SearchAlert).filter(SearchAlert.is_active == True).all()
        
        for alert in alerts:
            # Récupérer les nouvelles annonces
            listings = db.query(Listing).filter(
                Listing.postal_code == alert.postal_code,
                Listing.created_at > alert.last_notified
            ).all()
            
            if listings:
                user = db.query(User).filter(User.id == alert.user_id).first()
                notification_service.notify_new_listings(
                    user=user,
                    alert=alert,
                    listings=listings,
                    use_email=True
                )
    finally:
        db.close()
```

Planifier la tâche :

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'send-alerts-every-hour': {
        'task': 'app.tasks.send_alert_notifications',
        'schedule': crontab(minute=0),  # Toutes les heures
    },
}
```

### Option 2 : APScheduler

```bash
pip install apscheduler
```

Créer `backend/app/scheduler.py` :

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.notifications import notification_service
from app.database import SessionLocal
from app.models import User, SearchAlert, Listing

scheduler = BackgroundScheduler()

def send_alert_notifications_job():
    """Envoyer les notifications pour toutes les alertes actives."""
    db = SessionLocal()
    
    try:
        alerts = db.query(SearchAlert).filter(SearchAlert.is_active == True).all()
        
        for alert in alerts:
            listings = db.query(Listing).filter(
                Listing.postal_code == alert.postal_code,
                Listing.created_at > alert.last_notified
            ).all()
            
            if listings:
                user = db.query(User).filter(User.id == alert.user_id).first()
                notification_service.notify_new_listings(
                    user=user,
                    alert=alert,
                    listings=listings,
                    use_email=True
                )
    finally:
        db.close()

# Planifier la tâche toutes les heures
scheduler.add_job(send_alert_notifications_job, 'cron', minute=0)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
```

Intégrer dans `app/main.py` :

```python
from app.scheduler import start_scheduler, stop_scheduler

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
```

## 5. Templates Email Personnalisés

Créer `backend/app/email_templates.py` :

```python
def get_welcome_email_template(user_name: str) -> str:
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Bienvenue sur Real Estate Scraper!</h2>
            <p>Bonjour {user_name},</p>
            <p>Merci de vous être inscrit. Vous pouvez maintenant:</p>
            <ul>
                <li>Créer des alertes de recherche personnalisées</li>
                <li>Sauvegarder vos annonces favorites</li>
                <li>Recevoir des notifications pour les nouvelles annonces</li>
            </ul>
            <p><a href="https://yourdomain.com/dashboard">Accéder à mon tableau de bord</a></p>
        </body>
    </html>
    """

def get_new_listings_email_template(alert_name: str, listings: list) -> str:
    listings_html = ""
    for listing in listings:
        listings_html += f"""
        <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px;">
            <h3>{listing.title}</h3>
            <p><strong>Prix:</strong> {listing.price:,.0f}€</p>
            <p><strong>Surface:</strong> {listing.surface_area} m²</p>
            <p><a href="{listing.listing_url}">Voir l'annonce</a></p>
        </div>
        """
    
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Nouvelles annonces pour: {alert_name}</h2>
            {listings_html}
        </body>
    </html>
    """
```

## 6. Monitoring des Notifications

### Logs

```bash
# Vérifier les logs des notifications
tail -f /var/log/real-estate-scraper/notifications.log
```

### Métriques

Ajouter à `backend/app/main.py` :

```python
from prometheus_client import Counter, Histogram

email_sent_counter = Counter('emails_sent_total', 'Total emails sent')
sms_sent_counter = Counter('sms_sent_total', 'Total SMS sent')
notification_duration = Histogram('notification_duration_seconds', 'Notification duration')

@app.get("/metrics")
def metrics():
    return {
        "emails_sent": email_sent_counter._value.get(),
        "sms_sent": sms_sent_counter._value.get(),
    }
```

## 7. Troubleshooting

### Les emails ne s'envoient pas

1. Vérifier la configuration SMTP dans `.env`
2. Vérifier les logs : `tail -f /tmp/backend.log | grep -i email`
3. Tester la connexion SMTP manuellement
4. Vérifier que le mot de passe d'application Gmail est correct

### Les SMS ne s'envoient pas

1. Vérifier la configuration Twilio dans `.env`
2. Vérifier que le compte Twilio a des crédits
3. Vérifier le numéro de téléphone (format international)
4. Vérifier les logs Twilio dans la console

### Notifications en retard

1. Augmenter la fréquence du scheduler (ex: toutes les 15 minutes)
2. Vérifier que le serveur n'est pas surchargé
3. Vérifier les logs pour les erreurs de base de données

## 8. Ressources

- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [Twilio Documentation](https://www.twilio.com/docs)
- [Celery Documentation](https://docs.celeryproject.io/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
