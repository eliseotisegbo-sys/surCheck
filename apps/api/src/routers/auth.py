"""Router d'authentification pour SûrCheck AI.
Gère l'inscription, la connexion sécurisée par bcrypt & JWT, et le profil utilisateur.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from jose import jwt, JWTError

from ..config import settings
from ..schemas import UserRegister, UserLogin, TokenResponse
from ..services.supabase_db import supabase_db

router = APIRouter(prefix="/auth", tags=["Authentification"])

security = HTTPBearer(auto_error=False)

# Cache mémoire de repli si Supabase temporairement inaccessible
IN_MEMORY_USERS = {}


def hash_password(password: str) -> str:
    """Hache le mot de passe avec l'algorithme bcrypt sécurisé."""
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son empreinte bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    """Génère un JWT d'accès valide et signé pour l'utilisateur."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Extrait et valide l'utilisateur courant à partir du Bearer Token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session non authentifiée. Veuillez vous connecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expirée ou invalide.")

    # Récupération utilisateur depuis Supabase
    user = await supabase_db.get_user_by_id(user_id)
    if not user:
        # Repli mémoire
        user = next((u for u in IN_MEMORY_USERS.values() if u["id"] == user_id), None)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    """Crée un nouveau compte utilisateur avec 5 analyses gratuites offertes."""
    email_clean = user.email.strip().lower()

    # Vérification d'existence préalable
    existing_user = await supabase_db.get_user_by_email(email_clean)
    if existing_user or email_clean in IN_MEMORY_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette adresse email est déjà associée à un compte."
        )

    hashed = hash_password(user.password)

    # Persistance Supabase
    created = await supabase_db.create_user(
        name=user.name.strip(),
        email=email_clean,
        password_hash=hashed,
    )

    if created:
        user_id = created.get("id")
        user_name = created.get("name", user.name)
        free_quota = created.get("free_analyses_quota", 5)
        paid_credits = created.get("paid_credits_balance", 0)
    else:
        # Fallback mémoire résilient
        user_id = str(uuid.uuid4())
        user_name = user.name.strip()
        free_quota = 5
        paid_credits = 0
        IN_MEMORY_USERS[email_clean] = {
            "id": user_id,
            "name": user_name,
            "email": email_clean,
            "password_hash": hashed,
            "free_analyses_quota": free_quota,
            "paid_credits_balance": paid_credits,
            "role": "user",
        }

    token = create_access_token(user_id=str(user_id), email=email_clean)

    return TokenResponse(
        access_token=token,
        user_name=user_name,
        user_email=email_clean,
        free_quota=free_quota,
        paid_credits=paid_credits,
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Connecte un utilisateur existant."""
    email_clean = credentials.email.strip().lower()

    # Recherche Supabase d'abord
    user_record = await supabase_db.get_user_by_email(email_clean)
    if not user_record:
        user_record = IN_MEMORY_USERS.get(email_clean)

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects. Veuillez vérifier votre email et mot de passe."
        )

    if not verify_password(credentials.password, user_record.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects. Veuillez vérifier votre email et mot de passe."
        )

    user_id = str(user_record["id"])
    token = create_access_token(user_id=user_id, email=email_clean)

    return TokenResponse(
        access_token=token,
        user_name=user_record.get("name", "Utilisateur"),
        user_email=email_clean,
        free_quota=user_record.get("free_analyses_quota", 5),
        paid_credits=user_record.get("paid_credits_balance", 0),
    )


@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Consulte les informations du compte et le solde de quotas de l'utilisateur."""
    return {
        "id": current_user.get("id"),
        "name": current_user.get("name"),
        "email": current_user.get("email"),
        "role": current_user.get("role", "user"),
        "free_quota": current_user.get("free_analyses_quota", 5),
        "paid_credits": current_user.get("paid_credits_balance", 0),
    }


@router.get("/analyses")
async def get_my_analyses(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Récupère l'historique d'analyses sauvegardé de l'utilisateur."""
    user_id = str(current_user.get("id"))
    history = await supabase_db.get_user_analyses(user_id, limit=20)
    return history
