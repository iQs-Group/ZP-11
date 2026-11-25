"""ProofGate ZP-11 -- the Zero-Point release-governance standard.

Eleven independent, machine-verified zones sit between every change and ``main``.
The gate is closed by default and opens only when a change ships a reproducible,
signed Proof-Pack a third party can re-run. No evidence, no merge.

Invented by Naquib Hatami. Published as an open standard under the MIT License.
"""
from __future__ import annotations

from .crypto import KeyPair, PublicKey, digest, sha256_hex, sign, verify
from .pack import ProofPack, Receipt, VerifyReport, STANDARD, verify_pack
from .verdict import Verdict
from .zones import CANONICAL_TITLES, Context, Zone, ZoneResult, run_zone
from .gate import build_zones, load_config, run_gate

__all__ = [
    "KeyPair", "PublicKey", "digest", "sha256_hex", "sign", "verify",
    "ProofPack", "Receipt", "VerifyReport", "STANDARD", "verify_pack",
    "Verdict", "CANONICAL_TITLES", "Context", "Zone", "ZoneResult", "run_zone",
    "build_zones", "load_config", "run_gate",
    "__version__", "STANDARD_VERSION", "INVENTOR",
]

__version__ = "1.0.0"
STANDARD_VERSION = "zp11/v1"
INVENTOR = "Naquib Hatami"
