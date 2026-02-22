# Configuration des Variables d'Environnement

Guide complet pour configurer les variables d'environnement pour email, SMS, et autres services.

## 1. Configuration Email (Gmail)

### Étape 1 : Activer l'authentification à deux facteurs

1. Aller sur https://myaccount.google.com/security
2. Activer "Authentification à deux facteurs"
3. Cliquer sur "Mots de passe d'application"

### Étape 2 : Générer un mot de passe d'application

1. Sélectionner "Mail" et "Windows"
2. Google génère un mot de passe de 16 caractères
3. Copier ce mot de passe

### Étape 3 : Configurer le fichier .env

```bash
# Backend
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-password
FROM_EMAIL=your-email@gmail.com
```

### Étape 4 : Tester la connexion

```bash
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-16-char-password')
print('✓ SMTP connection successful')
server.quit()
"
```

## 2. Configuration SMS (Twilio)

### Étape 1 : Créer un compte Twilio

1. Aller sur https://www.twilio.com/console
2. S'inscrire ou se connecter
3. Obtenir votre Account SID et Auth Token

### Étape 2 : Acheter un numéro Twilio

1. Aller sur https://www.twilio.com/console/phone-numbers/incoming
2. Cliquer sur "Get a phone number"
3. Sélectionner un pays et un numéro
4. Copier le numéro

### Étape 3 : Configurer le fichier .env

```bash
# Backend
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

### Étape 4 : Tester la connexion

```bash
python3 -c "
from twilio.rest import Client

account_sid = 'your-account-sid'
auth_token = 'your-auth-token'
client = Client(account_sid, auth_token)

message = client.messages.create(
    body='Test SMS from Real Estate Scraper',
    from_='+1234567890',
    to='+33612345678'
)

print(f'✓ SMS sent: {message.sid}')
"
```

## 3. Configuration Base de Données

### PostgreSQL (Production)

```bash
# Backend
DATABASE_URL=postgresql://user:password@localhost:5432/real_estate_scraper
```

### SQLite (Développement)

```bash
# Backend
DATABASE_URL=sqlite:///./real_estate_scraper.db
```

## 4. Configuration Authentification

```bash
# Backend
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Générer une clé secrète sécurisée

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 5. Configuration API

```bash
# Backend
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Frontend
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

## 6. Configuration Redis (Cache)

```bash
# Backend
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-redis-password
```

## 7. Configuration Scraping

```bash
# Backend
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_DELAY=2
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Respect robots.txt
RESPECT_ROBOTS_TXT=true
THROTTLE_DELAY=1
```

## 8. Configuration Logging

```bash
# Backend
LOG_LEVEL=INFO
LOG_FILE=/var/log/real-estate-scraper.log
LOG_FORMAT=json
```

## 9. Configuration CORS

```bash
# Backend
CORS_ORIGINS=["http://localhost:5173","https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET","POST","PUT","DELETE"]
CORS_ALLOW_HEADERS=["*"]
```

## 10. Configuration Monitoring

```bash
# Backend
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
SENTRY_DSN=your-sentry-dsn
```

## 11. Fichier .env Complet (Développement)

```bash
# === DATABASE ===
DATABASE_URL=sqlite:///./real_estate_scraper.db

# === AUTHENTICATION ===
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# === EMAIL ===
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-password
FROM_EMAIL=your-email@gmail.com

# === SMS ===
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# === API ===
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# === FRONTEND ===
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# === REDIS ===
REDIS_URL=redis://localhost:6379/0

# === SCRAPING ===
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_DELAY=2
RESPECT_ROBOTS_TXT=true
THROTTLE_DELAY=1

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FILE=/var/log/real-estate-scraper.log

# === CORS ===
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# === MONITORING ===
PROMETHEUS_ENABLED=true
```

## 12. Fichier .env Complet (Production)

```bash
# === DATABASE ===
DATABASE_URL=postgresql://scraper:secure_password@db.example.com:5432/real_estate_scraper

# === AUTHENTICATION ===
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# === EMAIL ===
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-16-char-password
FROM_EMAIL=noreply@yourdomain.com

# === SMS ===
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# === API ===
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# === FRONTEND ===
VITE_API_URL=https://api.yourdomain.com
VITE_API_TIMEOUT=30000

# === REDIS ===
REDIS_URL=redis://redis.yourdomain.com:6379/0
REDIS_PASSWORD=secure_password

# === SCRAPING ===
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_DELAY=2
RESPECT_ROBOTS_TXT=true
THROTTLE_DELAY=1

# === LOGGING ===
LOG_LEVEL=WARNING
LOG_FILE=/var/log/real-estate-scraper.log

# === CORS ===
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# === MONITORING ===
PROMETHEUS_ENABLED=true
SENTRY_DSN=your-sentry-dsn
```

## 13. Charger les variables d'environnement

### Depuis un fichier .env

```bash
# Backend
cd backend
export $(cat .env | xargs)
python3 -m uvicorn app.main:app
```

### Depuis la ligne de commande

```bash
export SMTP_USER=your-email@gmail.com
export SMTP_PASSWORD=your-16-char-password
python3 -m uvicorn app.main:app
```

### Depuis Docker

```bash
docker run -e SMTP_USER=your-email@gmail.com \
           -e SMTP_PASSWORD=your-16-char-password \
           real-estate-scraper
```

## 14. Validation des variables

```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    'DATABASE_URL',
    'SECRET_KEY',
    'SMTP_SERVER',
    'SMTP_USER',
    'SMTP_PASSWORD',
]

missing = []
for var in required_vars:
    if not os.getenv(var):
        missing.append(var)

if missing:
    print(f"❌ Missing variables: {', '.join(missing)}")
else:
    print("✓ All required variables are set")
EOF
```

## 15. Sécurité

### Ne JAMAIS commiter le fichier .env

```bash
# Ajouter à .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.*.local" >> .gitignore
```

### Utiliser des secrets dans CI/CD

```yaml
# GitHub Actions
- name: Deploy
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
  run: ./deploy.sh
```

### Rotation des clés secrètes

```bash
# Générer une nouvelle clé
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Mettre à jour dans .env et redéployer
export SECRET_KEY=new-secret-key
python3 -m uvicorn app.main:app --reload
```

## 16. Troubleshooting

### Erreur : "SMTP authentication failed"

```bash
# Vérifier les identifiants
python3 -c "
import smtplib
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('your-email@gmail.com', 'your-password')
    print('✓ SMTP OK')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

### Erreur : "Twilio authentication failed"

```bash
# Vérifier les identifiants Twilio
python3 -c "
from twilio.rest import Client
try:
    client = Client('account_sid', 'auth_token')
    print('✓ Twilio OK')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

### Erreur : "Database connection failed"

```bash
# Vérifier la connexion PostgreSQL
psql -U user -d real_estate_scraper -h localhost -c "SELECT 1;"

# Ou avec SQLite
sqlite3 real_estate_scraper.db "SELECT 1;"
```

## 17. Ressources

- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [Twilio Console](https://www.twilio.com/console)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html)
- [Python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
