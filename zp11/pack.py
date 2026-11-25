"""The Proof-Pack: the single machine-verifiable record the gate emits.

A pack names the change, lists every zone's verdict and evidence, and carries a
signature chain. Two independent properties make it trustworthy without trusting
the pipeline that produced it:

* **Integrity** -- each zone receipt is digested over its canonical form and
  signed; altering any evidence byte invalidates the receipt's signature.
* **Seal** -- ZP-11 signs the ordered list of receipt digests together with the
  change, so a pack cannot be assembled from receipts that never shared a gate.

Verification needs nothing but the pack and a public key. ``verify`` returns a
structured :class:`VerifyReport`; the gate's decision is never a matter of trust.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .crypto import KeyPair, PublicKey, digest, sign, verify
from .verdict import Verdict

__all__ = ["Receipt", "ProofPack", "VerifyReport", "STANDARD"]

STANDARD = "zp11/v1"


def _receipt_body(id: str, title: str, verdict: str, evidence: dict) -> dict:
    return {"id": id, "title": title, "verdict": verdict, "evidence": evidence}


@dataclass
class Receipt:
    id: str
    title: str
    verdict: Verdict
    evidence: dict
    digest: str = ""
    signature: str = ""

    def body(self) -> dict:
        return _receipt_body(self.id, self.title, self.verdict.value, self.evidence)

    def signed_body(self) -> dict:
        return {**self.body(), "digest": self.digest}

    def finalize(self, keypair: Optional[KeyPair]) -> "Receipt":
        self.digest = digest(self.body())
        if keypair is not None:
            self.signature = sign(keypair, self.signed_body())
        return self

    def to_dict(self) -> dict:
        d = self.signed_body()
        if self.signature:
            d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Receipt":
        return cls(
            id=d["id"], title=d["title"], verdict=Verdict.coerce(d["verdict"])
            if hasattr(Verdict, "coerce") else Verdict(d["verdict"]),
            evidence=d.get("evidence", {}), digest=d.get("digest", ""),
            signature=d.get("signature", ""),
        )


def _seal_content(change: dict, created: str, receipts: list[Receipt],
                  passed: int, total: int, verdict: Verdict) -> dict:
    return {
        "standard": STANDARD,
        "created": created,
        "change": change,
        "verdict": verdict.value,
        "zones_passed": passed,
        "zones_total": total,
        "receipts": [{"id": r.id, "digest": r.digest} for r in receipts],
    }


@dataclass
class ProofPack:
    change: dict
    created: str
    receipts: list[Receipt] = field(default_factory=list)
    key_id: str = ""
    seal_signature: str = ""
    sealed: bool = False

    @property
    def verdict(self) -> Verdict:
        if not self.receipts:
            return Verdict.FAIL
        return Verdict.PASS if all(r.verdict for r in self.receipts) else Verdict.FAIL

    @property
    def passed(self) -> int:
        return sum(1 for r in self.receipts if r.verdict)

    def seal(self, keypair: KeyPair) -> "ProofPack":
        self.key_id = keypair.public.id
        for r in self.receipts:
            r.finalize(keypair)
        content = _seal_content(self.change, self.created, self.receipts,
                                self.passed, len(self.receipts), self.verdict)
        self.seal_signature = sign(keypair, content)
        self.sealed = self.verdict is Verdict.PASS
        return self

    def to_dict(self) -> dict:
        return {
            "standard": STANDARD,
            "created": self.created,
            "change": self.change,
            "zones": [r.to_dict() for r in self.receipts],
            "seal": {
                "verdict": self.verdict.value,
                "sealed": self.sealed,
                "zones_passed": self.passed,
                "zones_total": len(self.receipts),
                "key": self.key_id,
                "signature": self.seal_signature,
            },
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProofPack":
        receipts = [Receipt(id=z["id"], title=z["title"], verdict=Verdict(z["verdict"]),
                            evidence=z.get("evidence", {}), digest=z.get("digest", ""),
                            signature=z.get("signature", "")) for z in d.get("zones", [])]
        seal = d.get("seal", {})
        return cls(change=d.get("change", {}), created=d.get("created", ""),
                   receipts=receipts, key_id=seal.get("key", ""),
                   seal_signature=seal.get("signature", ""), sealed=bool(seal.get("sealed")))


@dataclass
class VerifyReport:
    ok: bool
    merge_permitted: bool
    reasons: list[str] = field(default_factory=list)
    zones_passed: int = 0
    zones_total: int = 0

    def __bool__(self) -> bool:
        return self.ok


_REQUIRED_ZONES = tuple(f"ZP-{i}" for i in range(1, 12))


def verify_pack(pack: ProofPack, public: Optional[PublicKey] = None,
                *, require_all_zones: bool = True) -> VerifyReport:
    """Verify integrity, the seal, and the fail-closed decision of a pack."""
    reasons: list[str] = []
    key = public or (PublicKey.parse(pack.key_id) if pack.key_id else None)

    ids = [r.id for r in pack.receipts]
    if require_all_zones:
        missing = [z for z in _REQUIRED_ZONES if z not in ids]
        if missing:
            reasons.append(f"missing zones: {', '.join(missing)}")

    for r in pack.receipts:
        if digest(r.body()) != r.digest:
            reasons.append(f"{r.id}: digest mismatch (evidence altered)")
        if key is not None:
            if not r.signature or not verify(key, r.signed_body(), r.signature):
                reasons.append(f"{r.id}: bad or missing signature")

    passed = pack.passed
    total = len(pack.receipts)

    if key is not None:
        content = _seal_content(pack.change, pack.created, pack.receipts,
                                passed, total, pack.verdict)
        if not pack.seal_signature or not verify(key, content, pack.seal_signature):
            reasons.append("seal signature invalid")
    else:
        reasons.append("no public key available to verify signatures")

    all_pass = total > 0 and passed == total
    if not all_pass:
        failed = [r.id for r in pack.receipts if not r.verdict]
        reasons.append("fail-closed: " + (", ".join(failed) + " did not pass"
                                          if failed else "no zones ran"))
    if all_pass and not pack.sealed:
        reasons.append("all zones pass but pack is not sealed")

    integrity_ok = not reasons
    merge = integrity_ok and all_pass and pack.sealed
    return VerifyReport(ok=integrity_ok, merge_permitted=merge, reasons=reasons,
                        zones_passed=passed, zones_total=total)
