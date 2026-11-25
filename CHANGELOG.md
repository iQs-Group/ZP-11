# Changelog

All notable changes to ZP‑11 are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project adheres to
Semantic Versioning.

## [1.0.0] — 2026-11-25

### Added
- The `zp11/v1` specification: eleven Zero‑Point zones, Proof‑Pack format,
  Ed25519 signature chain, and the verification algorithm (`SPEC.md`).
- Reference implementation: canonical serialization (RFC 8785), Ed25519 crypto,
  fail‑closed verdict semantics, the eleven zones, the gate, and the `zp11` CLI.
- JSON Schema for the Proof‑Pack.
- Conformance test suite.
- Self‑gating CI: the repository is governed by its own reference gate.

Invented and authored by Naquib Hatami.
