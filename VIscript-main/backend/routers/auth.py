import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import jwt
import bcrypt
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from models.schemas import LoginRequest, RegisterRequest, TokenResponse, UserProfile
from db.supabase_client import supabase_client

logger = logging.getLogger("visualiq.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24
MIN_PASSWORD_LENGTH = 8


def _hash_password(plain: str) -> str:
    """Hash a plaintext password using native bcrypt."""
    pw_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        pw_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except Exception as e:
        logger.warning(f"Bcrypt verification error: {e}")
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=JWT_EXPIRE_HOURS)
    
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    return payload

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please enter a valid email address.")
    if len(req.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )

    # Check if user already exists
    existing = await supabase_client.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists. Please sign in.")

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    user_name = (req.name or "").strip() or email.split("@")[0].capitalize()
    user_role = (req.role or "").strip() or "Surveillance Operator"
    password_hash = _hash_password(req.password)

    user_data = await supabase_client.insert_user(
        user_id=user_id,
        email=email,
        password_hash=password_hash,
        name=user_name,
        role=user_role
    )

    # Issue JWT token
    token_claims = {
        "sub": user_data["id"],
        "email": user_data["email"],
        "name": user_data["name"],
        "role": user_data["role"],
    }
    token = create_access_token(token_claims)
    logger.info(f"New user registered successfully: {email} ({user_name})")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRE_HOURS * 3600,
        user={
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data["role"],
        }
    )

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    email = req.email.strip().lower()
    password = req.password

    # Look up user from persistent store
    user_data = await supabase_client.get_user_by_email(email)
    if not user_data:
        logger.warning(f"Failed login attempt for unknown email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify bcrypt password hash
    if not _verify_password(password, user_data["password_hash"]):
        logger.warning(f"Failed login attempt (wrong password) for {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT
    token_claims = {
        "sub": user_data["id"],
        "email": user_data["email"],
        "name": user_data["name"],
        "role": user_data["role"],
    }
    token = create_access_token(token_claims)
    logger.info(f"User authenticated successfully: {email}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRE_HOURS * 3600,
        user={
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data["role"],
        }
    )

@router.get("/me", response_model=UserProfile)
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    return UserProfile(
        id=user.get("sub", "unknown"),
        email=user.get("email", ""),
        name=user.get("name", "Officer"),
        role=user.get("role", "Operator"),
    )
