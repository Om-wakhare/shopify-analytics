"""
Shopify Billing API — Recurring Application Charges.

Flow:
  1. POST /billing/subscribe?plan=starter  →  creates charge → returns Shopify approval URL
  2. Merchant approves on Shopify's billing page
  3. Shopify redirects → GET /billing/callback?charge_id=xxx
  4. We activate the charge → update platform_user → issue new JWT
  5. Redirect to frontend dashboard
"""
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.db_models import PlatformUser, ShopifyStore
from app.utils.jwt import TokenPayload, create_access_token, get_current_user

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/billing", tags=["billing"])

FRONTEND_URL = "https://shopify-analytics-igsp.vercel.app"

PLANS = {
    "starter": {
        "name":  "Starter",
        "price": 29.00,
        "trial_days": 14,
        "terms": "Up to 1 store, 6-month data history",
    },
    "growth": {
        "name":  "Growth",
        "price": 79.00,
        "trial_days": 14,
        "terms": "Up to 3 stores, 12-month history, cohort analysis",
    },
    "pro": {
        "name":  "Pro",
        "price": 199.00,
        "trial_days": 14,
        "terms": "Unlimited stores, full history, priority support",
    },
}


# ---------------------------------------------------------------------------
# Step 1 — Create recurring charge
# ---------------------------------------------------------------------------
@router.post("/subscribe")
async def subscribe(
    plan: str = Query(..., description="starter | growth | pro"),
    current: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Shopify recurring charge and return the approval URL."""
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}")

    plan_config = PLANS[plan]

    # Fetch store for access token
    result = await db.execute(
        select(ShopifyStore).where(ShopifyStore.shop_domain == current.shop_domain)
    )
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # Create recurring charge on Shopify
    charge_data = {
        "recurring_application_charge": {
            "name":           plan_config["name"],
            "price":          plan_config["price"],
            "return_url":     f"{settings.APP_BASE_URL}/billing/callback",
            "trial_days":     plan_config["trial_days"],
            "test":           True,   # Set False in production
        }
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"https://{store.shop_domain}/admin/api/{settings.SHOPIFY_API_VERSION}/recurring_application_charges.json",
            json=charge_data,
            headers={"X-Shopify-Access-Token": store.access_token},
        )
        if resp.status_code not in (200, 201):
            logger.error("Billing API error: %s %s", resp.status_code, resp.text)
            raise HTTPException(status_code=502, detail="Failed to create charge")

        charge = resp.json()["recurring_application_charge"]

    # Store pending charge ID
    user_result = await db.execute(
        select(PlatformUser).where(PlatformUser.store_id == store.id)
    )
    user = user_result.scalar_one_or_none()
    if user:
        user.shopify_charge_id     = charge["id"]
        user.shopify_charge_status = "pending"
        user.subscription_plan     = plan
        await db.flush()

    return {
        "confirmation_url": charge["confirmation_url"],
        "charge_id": charge["id"],
        "plan": plan,
    }


# ---------------------------------------------------------------------------
# Step 2 — Callback after merchant approves/declines
# ---------------------------------------------------------------------------
@router.get("/callback")
async def billing_callback(
    charge_id: int = Query(...),
    shop: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Activate the charge and redirect to dashboard with fresh JWT."""
    # Fetch store
    result = await db.execute(
        select(ShopifyStore).where(ShopifyStore.shop_domain == shop)
    )
    store = result.scalar_one_or_none()
    if not store:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=store_not_found")

    # Fetch charge status from Shopify
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"https://{shop}/admin/api/{settings.SHOPIFY_API_VERSION}/recurring_application_charges/{charge_id}.json",
            headers={"X-Shopify-Access-Token": store.access_token},
        )
        if resp.status_code != 200:
            return RedirectResponse(f"{FRONTEND_URL}/subscribe?error=charge_fetch_failed")
        charge = resp.json()["recurring_application_charge"]

    charge_status = charge.get("status")

    if charge_status == "accepted":
        # Activate charge
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(
                f"https://{shop}/admin/api/{settings.SHOPIFY_API_VERSION}/recurring_application_charges/{charge_id}/activate.json",
                headers={"X-Shopify-Access-Token": store.access_token},
                json={},
            )

    # Update platform user
    user_result = await db.execute(
        select(PlatformUser).where(PlatformUser.store_id == store.id)
    )
    user = user_result.scalar_one_or_none()

    if user:
        if charge_status == "accepted":
            user.subscription_status   = "active"
            user.shopify_charge_status  = "active"
            user.subscribed_at          = datetime.now(timezone.utc)
        else:
            user.subscription_status   = "trial"  # keep on trial if declined
            user.shopify_charge_status  = charge_status
        await db.flush()

    # Issue fresh JWT with updated subscription status
    token = create_access_token(
        store_id=store.id,
        shop_domain=store.shop_domain,
        subscription_status=user.subscription_status if user else "trial",
        trial_ends_at=user.trial_ends_at if user else None,
    )

    if charge_status == "accepted":
        return RedirectResponse(f"{FRONTEND_URL}/auth/success?token={token}&subscribed=true")
    else:
        return RedirectResponse(f"{FRONTEND_URL}/subscribe?error=declined")


# ---------------------------------------------------------------------------
# GET /billing/plans — return available plans
# ---------------------------------------------------------------------------
@router.get("/plans")
async def get_plans():
    return [
        {"id": k, **v} for k, v in PLANS.items()
    ]
