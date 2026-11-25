"""``zp11`` -- the reference command-line interface.

    zp11 keygen   [--out KEY]            generate an Ed25519 signing key
    zp11 zones                           list the eleven canonical zones
    zp11 run      [--config zp11.toml]   run the gate, emit a Proof-Pack
    zp11 verify   PACK [--key PUB]       verify integrity, seal and decision

``run`` exits 0 only when merge is permitted (a sealed, all-PASS pack); any
failure exits non-zero, which is what makes the CLI safe to wire as a required
status check. ``verify`` exits 0 only when the pack verifies and merge is
permitted.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .crypto import KeyPair, PublicKey
from .gate import load_config, run_gate
from .pack import ProofPack, verify_pack
from .zones import CANONICAL_TITLES


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_key(path: Path) -> KeyPair:
    seed = bytes.fromhex(path.read_text().strip())
    return KeyPair.from_seed(seed)


def cmd_keygen(args) -> int:
    kp = KeyPair.generate()
    if args.out:
        Path(args.out).write_text(kp.seed_hex)
        Path(str(args.out) + ".pub").write_text(kp.public.id)
    print(kp.public.id)
    if not args.out:
        print(kp.seed_hex, file=sys.stderr)
    return 0


def cmd_zones(args) -> int:
    for i in range(1, 12):
        zid = f"ZP-{i}"
        print(f"{zid:6} {CANONICAL_TITLES[zid]}")
    return 0


def cmd_run(args) -> int:
    root = Path(args.root).resolve()
    config = load_config(Path(args.config))
    kp = _load_key(Path(args.key)) if args.key else KeyPair.generate()
    now = args.now or _utcnow()
    pack = run_gate(root, config, kp, now=now)
    out = pack.to_dict()
    text = json.dumps(out, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text)
    else:
        print(text)
    permitted = out["seal"]["sealed"] and out["seal"]["verdict"] == "PASS"
    print(("PASS · MERGE PERMITTED" if permitted
           else "FAIL · GATE STAYS SHUT"), file=sys.stderr)
    return 0 if permitted else 1


def cmd_verify(args) -> int:
    data = json.loads(Path(args.pack).read_text())
    pack = ProofPack.from_dict(data)
    pub = PublicKey.parse(Path(args.key).read_text().strip()) if args.key else None
    report = verify_pack(pack, pub, require_all_zones=not args.partial)
    print(json.dumps({
        "integrity_ok": report.ok,
        "merge_permitted": report.merge_permitted,
        "zones_passed": report.zones_passed,
        "zones_total": report.zones_total,
        "reasons": report.reasons,
    }, indent=2))
    return 0 if report.merge_permitted else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zp11", description="ProofGate ZP-11 reference CLI")
    p.add_argument("--version", action="version", version=f"zp11 {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("keygen", help="generate an Ed25519 signing key")
    g.add_argument("--out", help="write the seed to this file (and <out>.pub)")
    g.set_defaults(func=cmd_keygen)

    z = sub.add_parser("zones", help="list the eleven canonical zones")
    z.set_defaults(func=cmd_zones)

    r = sub.add_parser("run", help="run the gate and emit a Proof-Pack")
    r.add_argument("--config", default="zp11.toml")
    r.add_argument("--root", default=".")
    r.add_argument("--key", help="signing key seed file")
    r.add_argument("--out", help="write the Proof-Pack here")
    r.add_argument("--now", help="override the timestamp (for reproducible runs)")
    r.set_defaults(func=cmd_run)

    v = sub.add_parser("verify", help="verify a Proof-Pack")
    v.add_argument("pack")
    v.add_argument("--key", help="public key file (defaults to the key in the pack)")
    v.add_argument("--partial", action="store_true", help="do not require all 11 zones")
    v.set_defaults(func=cmd_verify)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
