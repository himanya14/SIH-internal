import hashlib
import hmac
import os

from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app import models


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing from the .env file"
    )


ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


security = HTTPBearer()


# ---------- PASSWORD HASHING ----------

def hash_password(password: str) -> str:
    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600000
    )

    return (
        f"{salt.hex()}$"
        f"{password_hash.hex()}"
    )


def verify_password(
    plain_password: str,
    stored_password: str
) -> bool:
    try:
        salt_hex, stored_hash_hex = (
            stored_password.split("$")
        )

        salt = bytes.fromhex(
            salt_hex
        )

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            600000
        )

        return hmac.compare_digest(
            password_hash.hex(),
            stored_hash_hex
        )

    except (ValueError, TypeError):
        return False


# ---------- JWT ----------

def create_access_token(
    officer_id: str
) -> str:
    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": officer_id,
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(
    token: str
):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except JWTError:
        return None


# ---------- CURRENT OFFICER ----------

def get_current_officer(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    payload = decode_access_token(
        token
    )

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    officer_id = payload.get(
        "sub"
    )

    if not officer_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    officer = db.query(
        models.Officer
    ).filter(
        models.Officer.officer_id
        == officer_id
    ).first()

    if not officer:
        raise HTTPException(
            status_code=401,
            detail="Officer not found"
        )

    if officer.status != "Active":
        raise HTTPException(
            status_code=403,
            detail="Officer account is inactive"
        )

    return officer