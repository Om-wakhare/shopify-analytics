"""
JWT utilities for platform authentication.

Flow:
  1. Merchant completes Shopify OAuth
  2. We issue a signed JWT containing store_id, shop_domain, subscription_status
  3. Frontend stores JWT in localStorage
  4. All API calls send: Authorization: Bearer <token>
  5. FastAPI dependency decodes and validates the token
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()

ALGORITHM    = "HS256"
TOKEN_EXPIRY = timedelta(days=30)

bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Token payload model
# ---------------------------------------------------------------------------

class TokenPayload(BaseModel):
    store_id:            str
    shop_domain:         str
    subscription_status: str = "trial"   # trial | active | expired
    trial_ends_at:       Optional[str] = None
    exp:                 Optional[int] = None


# ---------------------------------------------------------------------------
# Issue token
# ---------------------------------------------------------------------------

def create_access_token(
    store_id: uuid.UUID,
    shop_domain: str,
    subscription_status: str = "trial",
    trial_ends_at: Optional[datetime] = None,
) -> str:
    expire = datetime.now(timezone.utc) + TOKEN_EXPIRY
    payload = {
        "store_id":            str(store_id),
        "shop_domain":         shop_domain,
        "subscription_status": subscription_status,
        "trial_ends_at":       trial_ends_at.isoformat() if trial_ends_at else None,
        "exp":                 expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Decode + validate token
# ---------------------------------------------------------------------------

def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> TokenPayload:
    """Require a valid JWT on protected routes."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[TokenPayload]:
    """Same as above but returns None instead of raising for public routes."""
    if not credentials:
        return None
    try:
        return decode_token(credentials.credentials)
    except HTTPException:
        return None
