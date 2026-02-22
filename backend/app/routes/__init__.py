"""Routes FastAPI pour l'application."""

from app.routes import agencies, listings, scraper, auth, user_features, maps

__all__ = ["agencies", "listings", "scraper", "auth", "user_features", "maps"]
