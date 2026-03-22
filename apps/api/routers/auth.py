import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import get_db
from services.email import welcome_email

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "changeme-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "43200"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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
    return token_data


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
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
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
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
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
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
