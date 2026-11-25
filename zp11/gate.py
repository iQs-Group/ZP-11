"""The fail-closed gate: run the zones, assemble and seal the Proof-Pack.

The gate is the only place the eleven zones are composed. It runs ZP-1..ZP-10,
derives ZP-11 (the seal) from whether every prior zone returned PASS, signs the
receipt chain, and emits a :class:`~zp11.pack.ProofPack`. If any zone is FAIL or
silent, the pack is still emitted -- as evidence of *why* the gate stays shut --
but it is never sealed, and merge is not permitted.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .crypto import KeyPair
from .pack import ProofPack, Receipt
from .verdict import Verdict
from .zones import CANONICAL_TITLES, Context, Zone, run_zone

__all__ = ["load_config", "run_gate"]

try:  # Python 3.11+
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover
    import tomli as _toml  # type: ignore


def load_config(path: Path) -> dict:
    with open(path, "rb") as fh:
        return _toml.load(fh)


def _zone_order(key: str) -> int:
    try:
        return int(key.split("-")[1])
    except Exception:
        return 999


def build_zones(config: dict) -> list[Zone]:
    raw = config.get("zones", {})
    zones = []
    for zid in sorted(raw, key=_zone_order):
        spec = raw[zid]
        title = spec.get("title", CANONICAL_TITLES.get(zid, zid))
        kind = spec.get("kind", "require")
        zones.append(Zone(id=zid, title=title, kind=kind, spec=spec))
    return zones


def run_gate(root: Path, config: dict, keypair: KeyPair, *, now: str) -> ProofPack:
    change = dict(config.get("change", {}))
    ctx = Context(root=root, change=change, now=now, env={})
    zones = build_zones(config)

    receipts: list[Receipt] = []
    prior_all_pass = True
    for zone in zones:
        if zone.kind == "seal":
            verdict = Verdict.PASS if prior_all_pass else Verdict.FAIL
            evidence = {
                "kind": "seal",
                "tool": "zp11-ref",
                "zones_passed": sum(1 for r in receipts if r.verdict),
                "zones_total": len(receipts),
                "all_prior_pass": prior_all_pass,
            }
            receipts.append(Receipt(zone.id, zone.canonical_title, verdict, evidence))
            continue
        result = run_zone(zone, ctx)
        prior_all_pass = prior_all_pass and bool(result.verdict)
        receipts.append(Receipt(zone.id, zone.canonical_title, result.verdict, result.evidence))

    pack = ProofPack(change=change, created=now, receipts=receipts)
    pack.seal(keypair)
    return pack
