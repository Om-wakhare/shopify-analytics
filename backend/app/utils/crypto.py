"""
Cryptographic helpers:
  - HMAC-SHA256 verification for Shopify webhooks
  - OAuth callback HMAC validation
  - State token generation (CSRF protection)
"""
import base64
import hashlib
import hmac
import secrets
import urllib.parse
from typing import Dict


def generate_state_token() -> str:
    """Generate a cryptographically-random OAuth state parameter."""
    return secrets.token_urlsafe(32)


def verify_webhook_signature(
    raw_body: bytes,
    shopify_hmac_header: str,
    api_secret: str,
) -> bool:
    """
    Validate the X-Shopify-Hmac-Sha256 header on incoming webhooks.

    Shopify signs the raw request body with HMAC-SHA256 using the
    app's API secret and base64-encodes the result.

    Returns True only if the computed digest matches the header value.
    Uses constant-time comparison to prevent timing attacks.
    """
    digest = hmac.new(
        api_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).digest()
    computed = base64.b64encode(digest).decode("utf-8")
    # hmac.compare_digest requires same types
    return hmac.compare_digest(computed, shopify_hmac_header)


def verify_oauth_hmac(params: Dict[str, str], api_secret: str) -> bool:
    """
    Validate the HMAC sent back on the OAuth callback.

    Process:
    1. Remove 'hmac' key from params.
    2. Sort remaining keys, build percent-encoded query string.
    3. HMAC-SHA256 with the API secret.
    4. Compare hex digest to the received hmac value.
    """
    received_hmac = params.pop("hmac", "")
    # Sort and encode remaining parameters
    sorted_params = sorted(params.items())
    message = "&".join(f"{k}={v}" for k, v in sorted_params)
    digest = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, received_hmac)
