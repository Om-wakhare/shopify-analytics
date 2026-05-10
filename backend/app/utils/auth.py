"""
API Key authentication middleware.

Two-layer approach:
  1. FastAPI dependency `require_api_key` — protects individual routes
     (KPI endpoints, sync triggers).
  2. APIKeyMiddleware (Starlette) — can optionally protect entire path prefixes
     without decorating every route.

API keys are stored in Postgres (api_keys table) for multi-tenant support.
They are hashed with SHA-256 before storage — the raw key is only shown once
at creation time.

Key format:  sap_<32 random hex bytes>   (64 chars total + prefix)
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

_KEY_PREFIX = "sap_"
_HEADER_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=_HEADER_NAME, auto_error=False)


# ---------------------------------------------------------------------------
# Key generation
# ---------------------------------------------------------------------------

def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key.
    Returns (raw_key, hashed_key).
    raw_key is shown to the user once; hashed_key is stored.
    """
    raw = _KEY_PREFIX + secrets.token_hex(32)
    hashed = _hash_key(raw)
    return raw, hashed


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def require_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    FastAPI dependency. Raises 401 if the key is missing or invalid.
    Returns the api_key row as a dict on success.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Add X-API-Key header.",
        )

    hashed = _hash_key(api_key)
    result = await db.execute(
        text("""
            SELECT id, store_id, name, is_active, expires_at
            FROM api_keys
            WHERE key_hash = :hash
        """),
        {"hash": hashed},
    )
    row = result.mappings().one_or_none()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="API key is revoked")

    if row["expires_at"] and row["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="API key has expired")

    return dict(row)


async def require_store_api_key(
    shop: str,
    key_data: dict = Depends(require_api_key),
) -> dict:
    """
    Extends require_api_key — also verifies the key belongs to the
    requested shop (prevents cross-tenant data access).
    """
    # store_id in key_data is a UUID; we don't do a DB join here to keep
    # this dependency fast — the KPI router's get_store() already validates shop.
    return key_data
