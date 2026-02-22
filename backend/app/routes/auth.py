"""
Routes d'authentification et gestion des utilisateurs.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import User
from app.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.notifications import notification_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Schémas Pydantic
class UserRegister(BaseModel):
    """Schéma d'enregistrement utilisateur."""
    email: EmailStr
    username: str
    password: str
    full_name: str = None


class UserLogin(BaseModel):
    """Schéma de connexion utilisateur."""
    username: str
    password: str


class Token(BaseModel):
    """Schéma du token JWT."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schéma de réponse utilisateur."""
    id: int
    email: str
    username: str
    full_name: str = None
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Enregistrer un nouvel utilisateur.

    Args:
        user_data: Données d'enregistrement
        db: Session de base de données

    Returns:
        Utilisateur créé

    Raises:
        HTTPException: Si l'email ou l'username existe déjà
    """
    # Vérifier si l'utilisateur existe
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Créer le nouvel utilisateur
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Envoyer un email de bienvenue (optionnel, ne pas bloquer si erreur)
    try:
        notification_service.send_welcome_notification(user)
    except Exception as e:
        print(f"Warning: Failed to send welcome email: {e}")

    return user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authentifier un utilisateur.

    Args:
        credentials: Identifiants de connexion
        db: Session de base de données

    Returns:
        Token JWT

    Raises:
        HTTPException: Si les identifiants sont invalides
    """
    # Trouver l'utilisateur
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Créer le token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Obtenir les informations de l'utilisateur courant.

    Args:
        current_user: Utilisateur authentifié

    Returns:
        Informations de l'utilisateur
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    user_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Mettre à jour les informations de l'utilisateur courant.

    Args:
        user_data: Données à mettre à jour
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Utilisateur mis à jour
    """
    # Mettre à jour les champs autorisés
    if "full_name" in user_data:
        current_user.full_name = user_data["full_name"]

    if "password" in user_data:
        current_user.hashed_password = get_password_hash(user_data["password"])

    db.commit()
    db.refresh(current_user)

    return current_user


@router.delete("/me")
def delete_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Supprimer le compte de l'utilisateur courant.

    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données

    Returns:
        Message de confirmation
    """
    db.delete(current_user)
    db.commit()

    return {"message": "Account deleted successfully"}
