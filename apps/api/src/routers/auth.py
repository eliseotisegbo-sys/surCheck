"""Router d'authentification sobre pour SûrCheck AI.
Gère l'inscription, la connexion et les quotas d'analyses gratuites.
"""

import uuid
import hashlib
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from ..schemas import UserRegister, UserLogin, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentification"])

# Stockage utilisateur en mémoire (avant Supabase)
IN_MEMORY_USERS = {}


def hash_password(password: str) -> str:
    """Hachage de mot de passe sécurisé."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    """Crée un nouveau compte utilisateur avec 5 analyses gratuites offertes."""
    email_clean = user.email.strip().lower()
    if email_clean in IN_MEMORY_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette adresse email est déjà associée à un compte."
        )

    user_id = str(uuid.uuid4())
    user_record = {
        "id": user_id,
        "name": user.name.strip(),
        "email": email_clean,
        "password_hash": hash_password(user.password),
        "free_quota": 5,
        "paid_credits": 0,
        "role": "user",
        "created_at": datetime.utcnow(),
    }
    IN_MEMORY_USERS[email_clean] = user_record

    return TokenResponse(
        access_token=f"mock_jwt_token_{user_id}",
        user_name=user_record["name"],
        user_email=user_record["email"],
        free_quota=user_record["free_quota"],
        paid_credits=user_record["paid_credits"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Connecte un utilisateur existant."""
    email_clean = credentials.email.strip().lower()
    user_record = IN_MEMORY_USERS.get(email_clean)

    if not user_record or user_record["password_hash"] != hash_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects. Veuillez vérifier votre email et mot de passe."
        )

    return TokenResponse(
        access_token=f"mock_jwt_token_{user_record['id']}",
        user_name=user_record["name"],
        user_email=user_record["email"],
        free_quota=user_record["free_quota"],
        paid_credits=user_record["paid_credits"],
    )
