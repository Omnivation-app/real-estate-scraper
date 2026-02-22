# Real Estate Scraper — TODO

## Back-end (FastAPI)
- [x] Configuration de la base de données PostgreSQL
- [x] Modèles SQLAlchemy (Agency, Listing, ScrapingLog, DomainConfig)
- [x] Schémas Pydantic pour validation
- [x] Module de conformité légale (robots.txt, throttling, RGPD)
- [x] Parser HTML pour extraction de données
- [x] Module de scraping principal
- [x] Routes FastAPI (agencies, listings, scraper)
- [x] Endpoints de santé et info
- [ ] Tests unitaires pour le scraper
- [ ] Gestion des erreurs améliorée
- [ ] Logging structuré
- [ ] Rate limiting avancé

## Front-end (React + Vite)
- [x] Configuration Vite + TypeScript
- [x] Service API (axios client)
- [x] Page de recherche principale
- [x] Formulaire de filtres
- [x] Affichage des résultats (grid de listings)
- [x] Affichage des agences
- [x] Styling CSS (responsive)
- [ ] Tests unitaires
- [ ] Pagination
- [ ] Tri des résultats
- [ ] Favoris/Sauvegarde
- [ ] Notifications
- [ ] Dark mode

## Infrastructure
- [x] Docker Compose (PostgreSQL)
- [x] Structure du projet
- [ ] CI/CD (GitHub Actions)
- [ ] Déploiement (Docker, Heroku, etc.)
- [ ] Documentation API (Swagger)
- [ ] Documentation utilisateur

## Scraping & Données
- [x] Scraper pour SeLoger, LeBonCoin, Immobilier.com
- [x] Extraction des mentions légales
- [x] Respect robots.txt
- [x] Throttling configurable
- [ ] Scraper supplémentaires (Orpi, Century21, etc.)
- [ ] Cache des données
- [ ] Mise à jour automatique
- [ ] Gestion des captchas

## Conformité Légale
- [x] Respect robots.txt
- [x] Throttling
- [x] RGPD (pas de données personnelles)
- [x] Configuration par domaine
- [ ] Mentions légales de l'application
- [ ] Politique de confidentialité
- [ ] Conditions d'utilisation

## Optimisations
- [ ] Mise en cache (Redis)
- [ ] Compression des images
- [ ] Pagination côté serveur
- [ ] Indexation des bases de données
- [ ] Requêtes optimisées

## Documentation
- [ ] README complet
- [ ] Guide d'installation
- [ ] Guide d'utilisation
- [ ] Documentation API (Swagger)
- [ ] Exemples de code
