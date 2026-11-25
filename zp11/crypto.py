"""Cryptographic primitives for the Zero-Point seal.

Verdicts are worthless if they can be forged after the fact, so every receipt
in a Proof-Pack is signed with Ed25519 (RFC 8032) and every digest is SHA-256
over the canonical serialization. Keys are handled as raw 32-byte values and
printed as ``ed25519:<hex>`` so a pack is self-describing and a verifier needs
nothing but the public key to check it.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .canonical import canonicalize

__all__ = ["sha256_hex", "digest", "KeyPair", "PublicKey", "sign", "verify"]


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value) -> str:
    """SHA-256 (hex) over the canonical form of a JSON-compatible value."""
    return "sha256:" + sha256_hex(canonicalize(value))


def _raw_public(pub: Ed25519PublicKey) -> bytes:
    return pub.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


@dataclass(frozen=True)
class PublicKey:
    raw: bytes

    @property
    def id(self) -> str:
        return "ed25519:" + self.raw.hex()

    @classmethod
    def parse(cls, text: str) -> "PublicKey":
        if not text.startswith("ed25519:"):
            raise ValueError("public key must be 'ed25519:<hex>'")
        return cls(bytes.fromhex(text.split(":", 1)[1]))

    def _obj(self) -> Ed25519PublicKey:
        return Ed25519PublicKey.from_public_bytes(self.raw)


@dataclass(frozen=True)
class KeyPair:
    _private: Ed25519PrivateKey

    @classmethod
    def generate(cls) -> "KeyPair":
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def from_seed(cls, seed: bytes) -> "KeyPair":
        if len(seed) != 32:
            raise ValueError("seed must be 32 bytes")
        return cls(Ed25519PrivateKey.from_private_bytes(seed))

    @property
    def public(self) -> PublicKey:
        return PublicKey(_raw_public(self._private.public_key()))

    @property
    def seed_hex(self) -> str:
        raw = self._private.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
        return raw.hex()

    def sign_bytes(self, data: bytes) -> str:
        return "ed25519:" + self._private.sign(data).hex()


def sign(keypair: KeyPair, value) -> str:
    """Sign the canonical form of ``value``; returns ``ed25519:<hex-signature>``."""
    return keypair.sign_bytes(canonicalize(value))


def verify(public: PublicKey, value, signature: str) -> bool:
    if not signature.startswith("ed25519:"):
        return False
    sig = bytes.fromhex(signature.split(":", 1)[1])
    try:
        public._obj().verify(sig, canonicalize(value))
        return True
    except Exception:
        return False
