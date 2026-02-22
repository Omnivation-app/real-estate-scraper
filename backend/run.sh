#!/bin/bash

# Script de démarrage du back-end FastAPI

echo "Starting Real Estate Scraper Backend..."
echo "======================================="

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

# Installer les dépendances
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Attendre que PostgreSQL soit prêt
echo "Waiting for PostgreSQL..."
sleep 5

# Initialiser la base de données
echo "Initializing database..."
python3 -c "from app.database import init_db; init_db()"

# Démarrer le serveur
echo "Starting FastAPI server on http://localhost:8000"
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
