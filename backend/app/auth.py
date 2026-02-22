"""
Module d'authentification avec JWT et gestion des favoris.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.requests import Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexte de hachage des mots de passe
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Schéma de sécurité
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier un mot de passe."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hacher un mot de passe."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Créer un token JWT.
    
    Args:
        data: Données à encoder
        expires_delta: Délai d'expiration personnalisé
        
    Returns:
        Token JWT
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Obtenir l'utilisateur courant à partir du token JWT.
    
    Args:
        credentials: Credentials HTTP Bearer
        db: Session de base de données
        
    Returns:
        Utilisateur
        
    Raises:
        HTTPException: Si le token est invalide
    """
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Récupérer le token du header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise credential_exception
        
        token = auth_header[7:]  # Enlever "Bearer "
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        
        if user_id is None:
            raise credential_exception
            
    except JWTError:
        raise credential_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credential_exception
    
    return user


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Obtenir l'utilisateur courant (optionnel).
    
    Si pas de token fourni, retourne None au lieu de lever une exception.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
