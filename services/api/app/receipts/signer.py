"""Cryptographic signing and verification for F-20 receipts.

Uses Ed25519 asymmetric cryptography.
The private key signs receipt verification payloads.
The public key verifies them on the public verification endpoint.
"""

import base64
import binascii
import json
import os
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

_PRIVATE_KEY_ENV = "AICTE_RECEIPT_SIGNING_KEY"
_DEFAULT_DEV_SEED = b"aicte_fdr_receipt_dev_key_32byte"


def get_signing_key() -> Ed25519PrivateKey:
    raw_env = os.environ.get(_PRIVATE_KEY_ENV)
    if raw_env:
        try:
            key_bytes = base64.b64decode(raw_env)
            if len(key_bytes) == 32:
                return Ed25519PrivateKey.from_private_bytes(key_bytes)
        except (ValueError, binascii.Error):
            pass
    return Ed25519PrivateKey.from_private_bytes(_DEFAULT_DEV_SEED)


def get_public_key() -> Ed25519PublicKey:
    return get_signing_key().public_key()


def sign_receipt_payload(payload: dict[str, Any]) -> str:
    """Serializes canonical JSON payload and signs with Ed25519.
    Returns base64url-encoded signature string.
    """
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    private_key = get_signing_key()
    signature = private_key.sign(canonical_bytes)
    return base64.urlsafe_b64encode(signature).decode("ascii")


def verify_receipt_signature(payload: dict[str, Any], signature_b64: str) -> bool:
    """Verifies Ed25519 signature over canonical JSON payload."""
    try:
        canonical_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        signature_bytes = base64.urlsafe_b64decode(signature_b64)
        public_key = get_public_key()
        public_key.verify(signature_bytes, canonical_bytes)
        return True
    except (InvalidSignature, ValueError, binascii.Error, TypeError):
        return False
