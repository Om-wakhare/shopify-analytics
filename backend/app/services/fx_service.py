"""
FX Rate Service — live currency conversion with Redis caching.

Data flow:
  1. Check Redis for a cached rate (TTL = 1 hour).
  2. On miss, fetch from Open Exchange Rates (or any JSON endpoint).
  3. Cache the full rates dict in Redis.
  4. Expose convert(amount, from_currency) → Decimal in USD.

Fallback: if the external API is unavailable, fall back to the
hardcoded static table so the pipeline never fails silently.

To use a different provider, only _fetch_rates_from_api() needs changing.
"""
from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Dict, Optional

import httpx
import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_CACHE_KEY = "fx:rates:usd_base"
_CACHE_TTL = 3600  # 1 hour

# Static fallback table (used when API is down)
_STATIC_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.27,
    "CAD": 0.74,
    "AUD": 0.65,
    "JPY": 0.0067,
    "INR": 0.012,
    "BRL": 0.20,
    "MXN": 0.058,
    "SGD": 0.74,
    "HKD": 0.13,
    "SEK": 0.096,
    "NOK": 0.094,
    "DKK": 0.146,
    "CHF": 1.12,
    "NZD": 0.61,
    "ZAR": 0.055,
    "AED": 0.27,
}


class FXService:
    """
    Async FX conversion service backed by Redis cache.
    Instantiate once and reuse across requests.
    """

    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client
        self._rates: Optional[Dict[str, float]] = None  # in-process cache

    async def convert_to_usd(
        self,
        amount: Decimal,
        from_currency: str,
    ) -> Optional[Decimal]:
        """
        Convert `amount` from `from_currency` to USD.
        Returns None if the currency is unknown.
        """
        if from_currency.upper() == "USD":
            return amount

        rates = await self._get_rates()
        rate = rates.get(from_currency.upper())
        if rate is None:
            logger.warning("Unknown currency: %s — skipping conversion", from_currency)
            return None

        return (amount * Decimal(str(rate))).quantize(Decimal("0.01"))

    async def get_rate(self, currency: str) -> Optional[float]:
        """Return the USD rate for a single currency."""
        rates = await self._get_rates()
        return rates.get(currency.upper())

    async def _get_rates(self) -> Dict[str, float]:
        # 1. In-process cache (valid for the lifetime of this instance)
        if self._rates:
            return self._rates

        # 2. Redis cache
        cached = await self._redis.get(_CACHE_KEY)
        if cached:
            self._rates = json.loads(cached)
            return self._rates

        # 3. Live fetch
        try:
            rates = await _fetch_rates_from_api()
            await self._redis.setex(_CACHE_KEY, _CACHE_TTL, json.dumps(rates))
            self._rates = rates
            logger.info("FX rates refreshed from API (%d currencies)", len(rates))
            return rates
        except Exception as exc:
            logger.warning("FX API unavailable (%s) — using static fallback rates", exc)
            return _STATIC_RATES


async def _fetch_rates_from_api() -> Dict[str, float]:
    """
    Fetch current rates from Open Exchange Rates free tier.
    Replace APP_ID and URL to use a different provider.

    Expects a JSON response with at least: { "rates": { "EUR": 0.92, ... } }
    where the base currency is USD.
    """
    # For the free tier of Open Exchange Rates:
    # https://openexchangerates.org/api/latest.json?app_id=YOUR_APP_ID
    #
    # For Fixer.io (EUR base, requires conversion):
    # https://data.fixer.io/api/latest?access_key=YOUR_KEY
    #
    # Using a public exchange rate API (no key required) as demo:
    url = "https://api.exchangerate-api.com/v4/latest/USD"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    rates: Dict[str, float] = data.get("rates", {})
    if not rates:
        raise ValueError("No rates returned from FX API")

    # Ensure USD is always 1.0
    rates["USD"] = 1.0
    return rates


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

_redis_pool: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    """Lazy-initialise the Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def get_fx_service() -> FXService:
    """FastAPI dependency — yields a ready FXService instance."""
    redis = get_redis()
    return FXService(redis)
