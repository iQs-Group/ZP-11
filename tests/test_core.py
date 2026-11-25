"""Conformance tests for the ZP-11 reference implementation."""
from __future__ import annotations

import copy

from zp11.canonical import canonicalize, CanonicalizationError
from zp11.crypto import KeyPair, PublicKey, digest, sign, verify
from zp11.gate import run_gate
from zp11.pack import ProofPack, verify_pack
from zp11.verdict import Verdict, coerce


NOW = "2026-01-01T00:00:00Z"


def _minimal_config(all_pass: bool = True) -> dict:
    # A self-contained config that needs no external tools, so the unit tests do
    # not recurse into pytest the way the repo's own zp11.toml intentionally does.
    zones = {}
    for i in range(1, 11):
        zones[f"ZP-{i}"] = {"kind": "require", "require": ["source_commit"]}
    if not all_pass:
        zones["ZP-6"] = {"kind": "require", "require": ["does_not_exist"]}
    zones["ZP-11"] = {"kind": "seal"}
    change = {"id": "c1", "source_commit": "abc123", "builder": "test"}
    return {"change": change, "zones": zones}


# --- canonical serialization -------------------------------------------------

def test_canonical_sorts_keys_and_is_stable():
    a = canonicalize({"b": 1, "a": 2})
    b = canonicalize({"a": 2, "b": 1})
    assert a == b == b'{"a":2,"b":1}'


def test_canonical_rejects_non_finite():
    try:
        canonicalize({"x": float("nan")})
        assert False, "expected CanonicalizationError"
    except CanonicalizationError:
        pass


# --- crypto ------------------------------------------------------------------

def test_sign_and_verify_roundtrip():
    kp = KeyPair.generate()
    value = {"hello": "world", "n": 1}
    sig = sign(kp, value)
    assert verify(kp.public, value, sig)
    assert not verify(kp.public, {"hello": "tampered"}, sig)


def test_public_key_parse_roundtrip():
    kp = KeyPair.generate()
    pid = kp.public.id
    assert PublicKey.parse(pid).id == pid


def test_digest_is_deterministic():
    assert digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1})


# --- verdict -----------------------------------------------------------------

def test_verdict_fail_closed_coercion():
    assert coerce("PASS") is Verdict.PASS
    assert coerce("pass") is Verdict.PASS
    assert coerce(True) is Verdict.PASS
    assert coerce(None) is Verdict.FAIL
    assert coerce("whatever") is Verdict.FAIL
    assert bool(Verdict.PASS) and not bool(Verdict.FAIL)


# --- gate + pack -------------------------------------------------------------

def test_gate_seals_when_all_zones_pass(tmp_path):
    kp = KeyPair.generate()
    pack = run_gate(tmp_path, _minimal_config(True), kp, now=NOW)
    assert pack.verdict is Verdict.PASS
    assert pack.sealed is True
    assert len(pack.receipts) == 11
    report = verify_pack(pack, kp.public)
    assert report.ok and report.merge_permitted
    assert report.zones_passed == 11


def test_gate_stays_shut_when_a_zone_fails(tmp_path):
    kp = KeyPair.generate()
    pack = run_gate(tmp_path, _minimal_config(False), kp, now=NOW)
    assert pack.verdict is Verdict.FAIL
    assert pack.sealed is False
    report = verify_pack(pack, kp.public)
    assert not report.merge_permitted


def test_tampering_with_evidence_is_detected(tmp_path):
    kp = KeyPair.generate()
    pack = run_gate(tmp_path, _minimal_config(True), kp, now=NOW)
    data = pack.to_dict()
    # Flip a verdict after the fact without re-signing.
    data["zones"][0]["verdict"] = "FAIL"
    tampered = ProofPack.from_dict(data)
    report = verify_pack(tampered, kp.public)
    assert not report.ok
    assert any("digest mismatch" in r or "signature" in r for r in report.reasons)


def test_pack_roundtrips_through_dict(tmp_path):
    kp = KeyPair.generate()
    pack = run_gate(tmp_path, _minimal_config(True), kp, now=NOW)
    again = ProofPack.from_dict(copy.deepcopy(pack.to_dict()))
    assert verify_pack(again, kp.public).merge_permitted


def test_verify_requires_all_eleven_zones(tmp_path):
    kp = KeyPair.generate()
    cfg = _minimal_config(True)
    del cfg["zones"]["ZP-5"]
    pack = run_gate(tmp_path, cfg, kp, now=NOW)
    report = verify_pack(pack, kp.public, require_all_zones=True)
    assert not report.ok
    assert any("missing zones" in r for r in report.reasons)
