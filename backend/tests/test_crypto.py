"""
Tests for HMAC verification helpers.
These are pure-function tests — no DB or network required.
"""
import base64
import hashlib
import hmac

import pytest

from app.utils.crypto import (
    generate_state_token,
    verify_oauth_hmac,
    verify_webhook_signature,
)

SECRET = "test_api_secret_abc123"


# ---------------------------------------------------------------------------
# Webhook HMAC
# ---------------------------------------------------------------------------

def _make_signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def test_webhook_signature_valid():
    body = b'{"id":12345,"email":"test@example.com"}'
    sig = _make_signature(body, SECRET)
    assert verify_webhook_signature(body, sig, SECRET) is True


def test_webhook_signature_wrong_body():
    body = b'{"id":12345}'
    sig = _make_signature(b'{"id":99999}', SECRET)
    assert verify_webhook_signature(body, sig, SECRET) is False


def test_webhook_signature_wrong_secret():
    body = b'{"id":12345}'
    sig = _make_signature(body, "wrong_secret")
    assert verify_webhook_signature(body, sig, SECRET) is False


def test_webhook_signature_empty_body():
    body = b""
    sig = _make_signature(body, SECRET)
    assert verify_webhook_signature(body, sig, SECRET) is True


def test_webhook_signature_tampered_header():
    body = b'{"id":12345}'
    sig = _make_signature(body, SECRET)
    tampered = sig[:-4] + "AAAA"
    assert verify_webhook_signature(body, tampered, SECRET) is False


# ---------------------------------------------------------------------------
# OAuth HMAC
# ---------------------------------------------------------------------------

def _make_oauth_hmac(params: dict, secret: str) -> str:
    """Reproduce Shopify's OAuth HMAC generation."""
    sorted_params = sorted(params.items())
    message = "&".join(f"{k}={v}" for k, v in sorted_params)
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def test_oauth_hmac_valid():
    params = {
        "shop": "test.myshopify.com",
        "code": "abc123",
        "state": "xyz",
        "timestamp": "1700000000",
    }
    params["hmac"] = _make_oauth_hmac(params, SECRET)
    assert verify_oauth_hmac(params, SECRET) is True


def test_oauth_hmac_tampered_param():
    params = {
        "shop": "test.myshopify.com",
        "code": "abc123",
        "state": "xyz",
        "timestamp": "1700000000",
    }
    params["hmac"] = _make_oauth_hmac(params, SECRET)
    params["shop"] = "evil.myshopify.com"  # tamper after signing
    assert verify_oauth_hmac(params, SECRET) is False


# ---------------------------------------------------------------------------
# State token
# ---------------------------------------------------------------------------

def test_state_token_is_unique():
    tokens = {generate_state_token() for _ in range(100)}
    assert len(tokens) == 100  # all unique


def test_state_token_length():
    token = generate_state_token()
    # token_urlsafe(32) produces ~43 base64 chars
    assert len(token) >= 40
