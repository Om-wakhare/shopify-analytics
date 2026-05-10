"""
Shopify OAuth 2.0 flow — SaaS multi-tenant model.

Flow:
  1. Merchant visits login page → enters shop domain
  2. Frontend calls GET /connect-shopify?shop=xxx.myshopify.com
  3. We redirect to Shopify OAuth screen
  4. Shopify redirects back → GET /auth/callback
  5. We verify HMAC, exchange code, save store, create platform user
  6. Issue JWT → redirect to frontend with token:
       http://localhost:3000/auth/success?token=<jwt>
  7. Frontend stores token → dashboard loads
"""
import logging
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.db_models import ShopifyStore, PlatformUser
from app.utils.crypto import generate_state_token, verify_oauth_hmac
from app.utils.jwt import create_access_token, get_current_user, TokenPayload

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["auth"])

_state_store: dict[str, str] = {}  # state_token → shop_domain

TRIAL_DAYS = 14
FRONTEND_URL = settings.APP_BASE_URL.replace(":8000", ":3000") if ":8000" in settings.APP_BASE_URL else "http://localhost:3000"


# ---------------------------------------------------------------------------
# Step 1 — Initiate OAuth
# ---------------------------------------------------------------------------
@router.get("/connect-shopify")
async def connect_shopify(shop: str = Query(..., description="mystore.myshopify.com")):
    shop = _normalize_shop(shop)
    state = generate_state_token()
    _state_store[state] = shop

    params = {
        "client_id": settings.SHOPIFY_API_KEY,
        "scope": settings.SHOPIFY_SCOPES,
        "redirect_uri": f"{settings.APP_BASE_URL}/auth/callback",
        "state": state,
    }
    auth_url = f"https://{shop}/admin/oauth/authorize?{urllib.parse.urlencode(params)}"
    logger.info("Redirecting shop=%s to Shopify OAuth", shop)
    return RedirectResponse(url=auth_url, status_code=302)


# ---------------------------------------------------------------------------
# Step 2 — OAuth Callback → Issue JWT → Redirect to frontend
# ---------------------------------------------------------------------------
@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    params = dict(request.query_params)

    # 1. Validate state
    state = params.get("state", "")
    shop  = params.get("shop", "")
    if _state_store.get(state) != shop:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=invalid_state", status_code=302)
    del _state_store[state]

    # 2. Verify HMAC
    params_copy = dict(params)
    if not verify_oauth_hmac(params_copy, settings.SHOPIFY_API_SECRET):
        return RedirectResponse(f"{FRONTEND_URL}/login?error=hmac_failed", status_code=302)

    # 3. Exchange code for access token
    code = params.get("code")
    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=no_code", status_code=302)

    try:
        access_token, scopes = await _exchange_code(shop, code)
    except Exception as e:
        logger.error("Token exchange failed: %s", e)
        return RedirectResponse(f"{FRONTEND_URL}/login?error=token_exchange_failed", status_code=302)

    # 4. Upsert store
    store = await _upsert_store(db, shop, access_token, scopes)

    # 5. Upsert platform user (create on first install, update on reinstall)
    user = await _upsert_platform_user(db, store)

    # 6. Register webhooks + kick off bulk sync
    from app.workers.tasks import register_webhooks_task, trigger_initial_sync_task
    register_webhooks_task.delay(str(store.id))
    trigger_initial_sync_task.delay(str(store.id))

    # 7. Issue JWT
    token = create_access_token(
        store_id=store.id,
        shop_domain=store.shop_domain,
        subscription_status=user.subscription_status,
        trial_ends_at=user.trial_ends_at,
    )

    logger.info("Store %s connected — redirecting to frontend", shop)
    # Redirect to frontend with token in URL fragment
    return RedirectResponse(
        f"{FRONTEND_URL}/auth/success?token={token}",
        status_code=302
    )


# ---------------------------------------------------------------------------
# GET /auth/me — return current user info from JWT
# ---------------------------------------------------------------------------
@router.get("/auth/me")
async def get_me(
    current: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlatformUser).where(
            PlatformUser.store_id == current.store_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "store_id":            str(user.store_id),
        "shop_domain":         current.shop_domain,
        "email":               user.email,
        "name":                user.name,
        "subscription_status": user.subscription_status,
        "subscription_plan":   user.subscription_plan,
        "trial_ends_at":       user.trial_ends_at,
        "subscribed_at":       user.subscribed_at,
    }


# ---------------------------------------------------------------------------
# POST /auth/logout — client just discards the JWT; this is for audit log
# ---------------------------------------------------------------------------
@router.post("/auth/logout")
async def logout(current: TokenPayload = Depends(get_current_user)):
    logger.info("Store %s logged out", current.shop_domain)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalize_shop(shop: str) -> str:
    shop = shop.strip().lower()
    if not shop.endswith(".myshopify.com"):
        raise HTTPException(status_code=400, detail="Invalid shop domain")
    if "/" in shop or shop.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid shop domain")
    return shop


async def _exchange_code(shop: str, code: str) -> tuple[str, str]:
    url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id":     settings.SHOPIFY_API_KEY,
        "client_secret": settings.SHOPIFY_API_SECRET,
        "code":          code,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")
        data = resp.json()
        return data["access_token"], data.get("scope", "")


async def _upsert_store(
    db: AsyncSession,
    shop_domain: str,
    access_token: str,
    scopes: str,
) -> ShopifyStore:
    result = await db.execute(
        select(ShopifyStore).where(ShopifyStore.shop_domain == shop_domain)
    )
    store = result.scalar_one_or_none()
    if store:
        store.access_token  = access_token
        store.scopes        = scopes
        store.deactivated_at = None
    else:
        store = ShopifyStore(shop_domain=shop_domain, access_token=access_token, scopes=scopes)
        db.add(store)
    await db.flush()
    return store


async def _upsert_platform_user(
    db: AsyncSession,
    store: ShopifyStore,
) -> PlatformUser:
    result = await db.execute(
        select(PlatformUser).where(PlatformUser.store_id == store.id)
    )
    user = result.scalar_one_or_none()
    if not user:
        trial_ends = datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS)
        user = PlatformUser(
            store_id=store.id,
            subscription_status="trial",
            trial_ends_at=trial_ends,
        )
        db.add(user)
        await db.flush()
        logger.info("New platform user created for store %s (trial until %s)", store.shop_domain, trial_ends.date())
    return user
