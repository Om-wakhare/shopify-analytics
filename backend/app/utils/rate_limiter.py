"""
Shopify REST API rate limiter.

Shopify uses a leaky-bucket model:
  • Each shop gets a bucket of 40 credits (default tier).
  • Each REST call costs 1 credit.
  • The bucket refills at 2 credits/second.
  • Response header: X-Shopify-Shop-Api-Call-Limit: used/max

For GraphQL (Bulk Operations), a separate cost-based system applies;
we handle that via retry-after logic in the client.
"""
import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_CALL_LIMIT_HEADER = "X-Shopify-Shop-Api-Call-Limit"
_RETRY_AFTER_HEADER = "Retry-After"
_THROTTLE_STATUS = 429


def _parse_call_limit(header_value: str) -> tuple[int, int]:
    """Parse '35/40' → (35, 40)."""
    match = re.match(r"(\d+)/(\d+)", header_value)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 40


async def handle_rate_limit_response(
    response: httpx.Response,
    retry_after_default: float = 2.0,
) -> Optional[float]:
    """
    Inspect the response headers and return how many seconds to wait
    before retrying, or None if no rate-limit was hit.
    """
    if response.status_code != _THROTTLE_STATUS:
        # Check if we're approaching the limit and should slow down
        call_limit = response.headers.get(_CALL_LIMIT_HEADER)
        if call_limit:
            used, maximum = _parse_call_limit(call_limit)
            utilization = used / maximum if maximum else 0
            if utilization >= 0.8:
                sleep = 0.5  # proactive throttle at 80% bucket
                logger.debug("API bucket at %.0f%% — sleeping %.1fs", utilization * 100, sleep)
                return sleep
        return None

    retry_after = response.headers.get(_RETRY_AFTER_HEADER)
    wait = float(retry_after) if retry_after else retry_after_default
    logger.warning("Rate limited (429). Waiting %.1f seconds.", wait)
    return wait


class RateLimitedClient:
    """
    Thin async HTTP client wrapper that automatically respects
    Shopify's rate limits with exponential back-off on 429 responses.
    """

    MAX_RETRIES = 5
    BASE_BACKOFF = 1.0
    MAX_BACKOFF = 60.0

    def __init__(self, base_url: str, access_token: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self._request("POST", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        backoff = self.BASE_BACKOFF
        for attempt in range(1, self.MAX_RETRIES + 1):
            response = await self._client.request(method, path, **kwargs)
            wait = await handle_rate_limit_response(response)
            if wait is not None:
                await asyncio.sleep(wait)
                backoff = min(backoff * 2, self.MAX_BACKOFF)
                continue
            response.raise_for_status()
            return response
        raise RuntimeError(f"Exceeded {self.MAX_RETRIES} retries for {method} {path}")

    async def aclose(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()
