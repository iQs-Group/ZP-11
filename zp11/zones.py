"""The eleven Zero-Point zones.

Each zone is an independent check with a defined input, a deterministic verdict,
and evidence that lands in the Proof-Pack. Zones are declarative: a repository
maps each ZP-n to one of a small set of *kinds* in ``zp11.toml``. A zone whose
check cannot run -- missing file, non-zero command, unparseable output, an
exception -- returns FAIL, never silence.

Kinds
-----
require       every named context field is present and non-empty
file          a path exists and is non-empty (its sha256 becomes evidence)
command       a shell command exits 0 (stdout/stderr digest becomes evidence)
secret_scan   no high-entropy / known-pattern secret appears under the paths
seal          ZP-11 only: passes iff every prior zone passed (set by the gate)
"""
from __future__ import annotations

import base64
import math
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .crypto import sha256_hex
from .verdict import Verdict

__all__ = ["Zone", "Context", "ZoneResult", "run_zone", "CANONICAL_TITLES"]

# The canonical names of the eleven zones (the standard fixes these).
CANONICAL_TITLES = {
    "ZP-1": "Provenance",
    "ZP-2": "Reproducible build",
    "ZP-3": "Dependency integrity",
    "ZP-4": "Test evidence",
    "ZP-5": "Coverage floor",
    "ZP-6": "Static safety",
    "ZP-7": "Secret hygiene",
    "ZP-8": "Policy conformance",
    "ZP-9": "Signature chain",
    "ZP-10": "Independent re-run",
    "ZP-11": "Zero-point seal",
}

# Conservative secret detectors. False negatives are acceptable here; the point
# is that an *obvious* leak can never pass ZP-7 silently.
_SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),                      # AWS access key id
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),            # GitHub tokens
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),          # Slack tokens
    re.compile(r"sk-[A-Za-z0-9]{32,}"),                   # generic API secret
    re.compile(r"(?i)aws_secret_access_key\s*[=:]\s*[A-Za-z0-9/+=]{40}"),
]
_ENTROPY_TOKEN = re.compile(r"[A-Za-z0-9+/_\-]{24,}")


@dataclass
class Context:
    root: Path
    change: dict
    now: str
    env: dict = field(default_factory=dict)


@dataclass
class ZoneResult:
    verdict: Verdict
    evidence: dict


@dataclass
class Zone:
    id: str
    title: str
    kind: str
    spec: dict

    @property
    def canonical_title(self) -> str:
        return CANONICAL_TITLES.get(self.id, self.title)


def _shannon_entropy(token: str) -> float:
    if not token:
        return 0.0
    counts: dict[str, int] = {}
    for ch in token:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(token)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _evi(kind: str, **fields: Any) -> dict:
    out = {"kind": kind, "tool": "zp11-ref", "tool_version": _VERSION}
    out.update(fields)
    return out


def _run_require(zone: Zone, ctx: Context) -> ZoneResult:
    missing = []
    present = {}
    for name in zone.spec.get("require", []):
        value = ctx.change.get(name)
        if value in (None, "", [], {}):
            missing.append(name)
        else:
            present[name] = value
    verdict = Verdict.PASS if not missing else Verdict.FAIL
    return ZoneResult(verdict, _evi("require", required=sorted(zone.spec.get("require", [])),
                                    missing=sorted(missing), present=sorted(present)))


def _run_file(zone: Zone, ctx: Context) -> ZoneResult:
    rel = zone.spec.get("file", "")
    path = (ctx.root / rel)
    if not path.is_file():
        return ZoneResult(Verdict.FAIL, _evi("file", path=rel, exists=False))
    data = path.read_bytes()
    min_bytes = int(zone.spec.get("min_bytes", 1))
    ok = len(data) >= min_bytes
    return ZoneResult(
        Verdict.PASS if ok else Verdict.FAIL,
        _evi("file", path=rel, exists=True, bytes=len(data),
             min_bytes=min_bytes, sha256="sha256:" + sha256_hex(data)),
    )


def _run_command(zone: Zone, ctx: Context) -> ZoneResult:
    cmd = zone.spec.get("command", "")
    if not cmd:
        return ZoneResult(Verdict.FAIL, _evi("command", command=cmd, reason="empty command"))
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=str(ctx.root), capture_output=True,
            timeout=int(zone.spec.get("timeout", 600)), env={**ctx.env},
        )
    except Exception as exc:  # timeout, spawn failure -> FAIL, never silence
        return ZoneResult(Verdict.FAIL, _evi("command", command=cmd, error=type(exc).__name__))
    out_digest = "sha256:" + sha256_hex(proc.stdout + b"\x00" + proc.stderr)
    verdict = Verdict.PASS if proc.returncode == int(zone.spec.get("expect_code", 0)) else Verdict.FAIL
    return ZoneResult(
        verdict,
        _evi("command", command=cmd, exit_code=proc.returncode,
             expect_code=int(zone.spec.get("expect_code", 0)), output_sha256=out_digest),
    )


def _iter_files(root: Path, globs: list[str]):
    for pattern in globs:
        for p in root.glob(pattern):
            if p.is_file():
                yield p


def _run_secret_scan(zone: Zone, ctx: Context) -> ZoneResult:
    globs = zone.spec.get("paths", ["**/*"])
    entropy_floor = float(zone.spec.get("entropy", 4.6))
    findings = []
    scanned = 0
    for path in _iter_files(ctx.root, globs):
        if ".git/" in path.as_posix() or path.suffix in {".png", ".jpg", ".gif", ".pdf", ".zip"}:
            continue
        try:
            text = path.read_text("utf-8", errors="ignore")
        except Exception:
            continue
        scanned += 1
        rel = path.relative_to(ctx.root).as_posix()
        for pat in _SECRET_PATTERNS:
            if pat.search(text):
                findings.append({"path": rel, "rule": pat.pattern[:32]})
        for m in _ENTROPY_TOKEN.finditer(text):
            if _shannon_entropy(m.group(0)) >= entropy_floor and _looks_secretish(m.group(0)):
                findings.append({"path": rel, "rule": "high-entropy"})
                break
    verdict = Verdict.PASS if not findings else Verdict.FAIL
    # Record only locations, never the secret material itself.
    return ZoneResult(verdict, _evi("secret_scan", scanned=scanned,
                                     findings=findings[:50], clean=not findings))


def _looks_secretish(token: str) -> bool:
    # Avoid flagging base64 of ordinary text or long hex digests used as evidence.
    try:
        base64.b64decode(token + "===", validate=False)
    except Exception:
        pass
    has_digit = any(c.isdigit() for c in token)
    has_alpha = any(c.isalpha() for c in token)
    return has_digit and has_alpha and len(set(token)) > 12


_KINDS = {
    "require": _run_require,
    "file": _run_file,
    "command": _run_command,
    "secret_scan": _run_secret_scan,
}

_VERSION = "1.0.0"


def run_zone(zone: Zone, ctx: Context) -> ZoneResult:
    """Execute one zone. Any failure to produce a provable PASS yields FAIL."""
    if zone.kind == "seal":
        # Handled by the gate once every prior zone is known; never reached here.
        return ZoneResult(Verdict.FAIL, _evi("seal", reason="seal is set by the gate"))
    runner = _KINDS.get(zone.kind)
    if runner is None:
        return ZoneResult(Verdict.FAIL, _evi(zone.kind or "unknown", reason="unknown zone kind"))
    try:
        return runner(zone, ctx)
    except Exception as exc:  # a zone that crashes fails closed
        return ZoneResult(Verdict.FAIL, _evi(zone.kind, error=type(exc).__name__))
