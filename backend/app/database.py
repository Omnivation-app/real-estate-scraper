"""
Configuration de la base de données PostgreSQL.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator

# Configuration de la base de données
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./real_estate_scraper.db"  # SQLite par défaut pour le développement
)

# Créer le moteur SQLAlchemy
if DATABASE_URL.startswith("sqlite"):
    # SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )
else:
    # PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Désactiver le pooling pour éviter les problèmes de connexion
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL si SQL_ECHO=true
    )

# Créer la session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dépendance FastAPI pour obtenir une session de base de données.
    
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialiser la base de données (créer les tables)."""
    from app.models import Base
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Supprimer toutes les tables (à utiliser avec prudence)."""
    from app.models import Base
    Base.metadata.drop_all(bind=engine)
