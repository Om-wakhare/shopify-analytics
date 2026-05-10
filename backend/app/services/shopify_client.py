"""
Shopify API client — wraps both REST (Admin) and GraphQL endpoints.

Responsibilities:
  • Build correctly versioned URLs
  • Attach authentication headers
  • Delegate rate-limit handling to RateLimitedClient
  • Provide cursor-based pagination for REST endpoints
  • Execute GraphQL mutations / queries
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from app.config import get_settings
from app.utils.rate_limiter import RateLimitedClient

logger = logging.getLogger(__name__)
settings = get_settings()

_API_VERSION = settings.SHOPIFY_API_VERSION


class ShopifyClient: 
    """
    Async Shopify client for a single store.

    Usage:
        async with ShopifyClient(shop_domain, access_token) as client:
            async for page in client.paginate_orders():
                process(page)
    """

    def __init__(self, shop_domain: str, access_token: str):
        self.shop_domain = shop_domain
        self.access_token = access_token
        base_url = f"https://{shop_domain}/admin/api/{_API_VERSION}"
        self._http = RateLimitedClient(base_url=base_url, access_token=access_token)

    # ── REST: paginated fetchers ─────────────────────────────────────────

    async def paginate_customers(
        self,
        since_id: Optional[int] = None,
        updated_at_min: Optional[str] = None,
        limit: int = 250,
    ) -> AsyncGenerator[List[dict], None]:
        """Yield pages of customer dicts using cursor-based (link-header) pagination."""
        params: Dict[str, str | int] = {"limit": limit, "fields": CUSTOMER_FIELDS}
        if since_id:
            params["since_id"] = since_id
        if updated_at_min:
            params["updated_at_min"] = updated_at_min

        async for page in self._paginate("/customers.json", "customers", params):
            yield page

    async def paginate_orders(
        self,
        since_id: Optional[int] = None,
        updated_at_min: Optional[str] = None,
        status: str = "any",
        limit: int = 250,
    ) -> AsyncGenerator[List[dict], None]:
        """Yield pages of order dicts using cursor-based pagination."""
        params: Dict[str, str | int] = {
            "limit": limit,
            "status": status,
            "fields": ORDER_FIELDS,
        }
        if since_id:
            params["since_id"] = since_id
        if updated_at_min:
            params["updated_at_min"] = updated_at_min

        async for page in self._paginate("/orders.json", "orders", params):
            yield page

    async def _paginate(
        self,
        path: str,
        key: str,
        params: dict,
    ) -> AsyncGenerator[List[dict], None]:
        """
        Generic cursor-based paginator.
        Follows the Link header returned by Shopify (rel="next").
        """
        url: Optional[str] = path
        current_params: Optional[dict] = params

        while url:
            resp = await self._http.get(url, params=current_params)
            data = resp.json()
            items = data.get(key, [])
            if items:
                yield items

            # Parse Link header for next cursor
            url = _parse_next_link(resp.headers.get("Link", ""))
            current_params = None  # cursor URL includes all params

    # ── GraphQL ──────────────────────────────────────────────────────────

    async def graphql(self, query: str, variables: Optional[dict] = None) -> dict:
        """Execute a GraphQL query/mutation against the Admin API."""
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables

        resp = await self._http.post("/graphql.json", json=payload)
        result = resp.json()

        errors = result.get("errors")
        if errors:
            raise ShopifyGraphQLError(errors)

        return result.get("data", {})

    # ── Bulk Operations ──────────────────────────────────────────────────

    async def start_bulk_operation(self, bulk_query: str) -> str:
        """
        Submit a bulk operation and return the Shopify GID (global ID).
        """
        mutation = """
        mutation bulkOperationRunQuery($query: String!) {
          bulkOperationRunQuery(query: $query) {
            bulkOperation {
              id
              status
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        data = await self.graphql(mutation, variables={"query": bulk_query})
        op_data = data.get("bulkOperationRunQuery", {})
        errors = op_data.get("userErrors", [])
        if errors:
            raise ShopifyBulkOperationError(errors)
        return op_data["bulkOperation"]["id"]

    async def poll_bulk_operation(self, gid: str) -> dict:
        """
        Poll a bulk operation by GID.
        Returns the full bulkOperation object including status and url.
        """
        query = """
        query ($id: ID!) {
          node(id: $id) {
            ... on BulkOperation {
              id
              status
              errorCode
              objectCount
              fileSize
              url
              partialDataUrl
            }
          }
        }
        """
        data = await self.graphql(query, variables={"id": gid})
        return data.get("node", {})

    async def wait_for_bulk_operation(
        self,
        gid: str,
        poll_interval: int = 10,
        max_wait: int = 3600,
    ) -> str:
        """
        Block until the bulk operation completes.
        Returns the JSONL download URL.
        Raises on failure or timeout.
        """
        elapsed = 0
        while elapsed < max_wait:
            op = await self.poll_bulk_operation(gid)
            status = op.get("status")
            logger.info("Bulk op %s status=%s objects=%s", gid, status, op.get("objectCount"))

            if status == "COMPLETED":
                return op["url"]
            if status in ("FAILED", "CANCELED"):
                error_code = op.get("errorCode", "UNKNOWN")
                raise ShopifyBulkOperationError(
                    [{"message": f"Bulk operation {status}: {error_code}"}]
                )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Bulk operation {gid} did not complete within {max_wait}s")

    # ── Webhook registration ─────────────────────────────────────────────

    async def register_webhooks(self, app_base_url: str) -> List[dict]:
        """Register all required webhook subscriptions for this store."""
        topics = [
            "orders/create",
            "orders/updated",
            "customers/create",
            "customers/update",
            "app/uninstalled",
        ]
        results = []
        for topic in topics:
            result = await self._register_webhook(topic, app_base_url)
            results.append(result)
        return results

    async def _register_webhook(self, topic: str, app_base_url: str) -> dict:
        endpoint = topic.replace("/", "_")
        webhook_url = f"{app_base_url}/webhooks/{endpoint}"
        mutation = """
        mutation webhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
          webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
            webhookSubscription {
              id
              topic
              endpoint {
                __typename
                ... on WebhookHttpEndpoint {
                  callbackUrl
                }
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        gql_topic = topic.replace("/", "_").upper()
        variables = {
            "topic": gql_topic,
            "webhookSubscription": {
                "callbackUrl": webhook_url,
                "format": "JSON",
            },
        }
        data = await self.graphql(mutation, variables=variables)
        result = data.get("webhookSubscriptionCreate", {})
        errors = result.get("userErrors", [])
        if errors:
            logger.warning("Webhook registration warning for %s: %s", topic, errors)
        return result.get("webhookSubscription", {})

    # ── Context manager ──────────────────────────────────────────────────

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._http.aclose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_next_link(link_header: str) -> Optional[str]:
    """
    Parse Shopify's Link header and extract the 'next' cursor URL.

    Example:
      <https://...?page_info=abc>; rel="next", <...>; rel="previous"
    """
    if not link_header:
        return None
    for part in link_header.split(","):
        part = part.strip()
        if 'rel="next"' in part:
            url = part.split(";")[0].strip().lstrip("<").rstrip(">")
            return url
    return None


# Fields to fetch from REST API (minimize payload size)
CUSTOMER_FIELDS = "id,email,phone,created_at,updated_at,total_spent,orders_count,currency,tags,accepts_marketing,verified_email"
ORDER_FIELDS = "id,order_number,email,customer,line_items,total_price,subtotal_price,total_tax,total_discounts,currency,financial_status,fulfillment_status,cancel_reason,cancelled_at,source_name,landing_site,referring_site,created_at,updated_at,processed_at"


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ShopifyGraphQLError(Exception):
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(str(errors))


class ShopifyBulkOperationError(Exception):
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(str(errors))
