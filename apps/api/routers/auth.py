import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import uuid
import hashlib
import bcrypt as _bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from database import get_db
from services.email import welcome_email

router = APIRouter()

# ─── Rate Limiting ───────────────────────────────────────────────────────────
# Simple in-memory IP-based rate limiter (resets on process restart)
_rate_limit: dict[str, list[float]] = {}


def check_rate_limit(ip: str, key: str, max_calls: int, window_secs: int) -> None:
    """Raise 429 if IP has exceeded max_calls within window_secs."""
    now = time.monotonic()
    bucket_key = f"{ip}:{key}"
    timestamps = _rate_limit.get(bucket_key, [])
    # Drop expired timestamps
    timestamps = [t for t in timestamps if now - t < window_secs]
    if len(timestamps) >= max_calls:
        retry_after = int(window_secs - (now - timestamps[0]))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    timestamps.append(now)
    _rate_limit[bucket_key] = timestamps

SECRET_KEY = os.getenv("SECRET_KEY", "changeme-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    role: str = "artist"


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None


def hash_password(password: str) -> str:
    # Use bcrypt directly — avoids passlib/bcrypt version conflicts
    pw = password.encode("utf-8")[:72]
    return _bcrypt.hashpw(pw, _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pw = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
        return _bcrypt.checkpw(pw, hashed_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _hash_token(token: str) -> str:
    """SHA-256 hash of raw JWT for session table storage."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, role=payload.get("role"))
    except JWTError:
        raise credentials_exception

    # BUG FIX: Check session is not revoked in DB
    from sqlalchemy import text as _text
    token_hash = _hash_token(token)
    try:
        sess = await db.execute(
            _text(
                "SELECT id FROM sessions WHERE token_hash = :h "
                "AND revoked_at IS NULL AND expires_at > NOW() LIMIT 1"
            ),
            {"h": token_hash},
        )
        if not sess.fetchone():
            raise credentials_exception
    except HTTPException:
        raise
    except Exception:
        # If sessions table query fails (e.g. table not yet migrated), allow through
        # but log the issue
        import logging as _logging
        _logging.getLogger(__name__).warning("Session table check failed — allowing token through")

    return token_data


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    check_rate_limit(request.client.host, "register", max_calls=5, window_secs=300)
    if not user_in.email and not user_in.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or phone required",
        )

    valid_roles = {"owner", "artist", "producer", "developer"}
    if user_in.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of: {', '.join(valid_roles)}",
        )

    user_id = str(uuid.uuid4())
    password_hash = hash_password(user_in.password)

    from sqlalchemy import text
    await db.execute(
        text(
            """
            INSERT INTO users (id, email, phone, password_hash, role)
            VALUES (:id, :email, :phone, :password_hash, :role)
            """
        ),
        {
            "id": user_id,
            "email": user_in.email,
            "phone": user_in.phone,
            "password_hash": password_hash,
            "role": user_in.role,
        },
    )
    await db.commit()

    if user_in.email:
        asyncio.create_task(welcome_email(user_in.email))

    access_token = create_access_token(
        data={"sub": user_id, "role": user_in.role}
    )
    # Write session record for revocation support
    token_hash = _hash_token(access_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    try:
        await db.execute(
            text("""
                INSERT INTO sessions (id, user_id, token_hash, ip_address, expires_at)
                VALUES (:id, CAST(:user_id AS UUID), :token_hash, :ip, :expires_at)
            """),
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "token_hash": token_hash,
                "ip": request.client.host if request.client else None,
                "expires_at": expires_at,
            },
        )
        await db.commit()
    except Exception:
        pass  # Non-fatal

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/token", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    check_rate_limit(request.client.host, "login", max_calls=10, window_secs=60)
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT id, password_hash, role, status, locked_until FROM users WHERE email = :email"),
        {"email": form_data.username},
    )
    user = result.fetchone()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily locked",
        )

    await db.execute(
        text("UPDATE users SET last_login_at = NOW(), failed_attempts = 0 WHERE id = :id"),
        {"id": str(user.id)},
    )
    await db.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )

    # BUG FIX: Write session to DB so it can be revoked on logout
    token_hash = _hash_token(access_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    try:
        await db.execute(
            text("""
                INSERT INTO sessions (id, user_id, token_hash, ip_address, expires_at)
                VALUES (:id, CAST(:user_id AS UUID), :token_hash, :ip, :expires_at)
            """),
            {
                "id": str(uuid.uuid4()),
                "user_id": str(user.id),
                "token_hash": token_hash,
                "ip": request.client.host if request.client else None,
                "expires_at": expires_at,
            },
        )
        await db.commit()
    except Exception as e:
        # Non-fatal: session table write failure doesn't block login
        import logging as _l
        _l.getLogger(__name__).warning(f"Session write failed (non-fatal): {e}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # BUG FIX: Revoke session in DB so token cannot be reused
    from sqlalchemy import text
    token_hash = _hash_token(token)
    try:
        await db.execute(
            text("UPDATE sessions SET revoked_at = NOW() WHERE token_hash = :h AND revoked_at IS NULL"),
            {"h": token_hash},
        )
        await db.commit()
    except Exception as e:
        import logging as _l
        _l.getLogger(__name__).warning(f"Session revoke failed: {e}")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def me(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT id, email, role FROM users WHERE id = :id"),
        {"id": current_user.user_id},
    )
    user = result.fetchone()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"id": str(user.id), "email": user.email, "role": user.role}
