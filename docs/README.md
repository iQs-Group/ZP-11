# ProofGate ZP-11 — Documentation

The complete documentation set for ProofGate ZP-11, the open, fail-closed
release-governance standard. The documents below are grouped by theme; each links
to its source file in this directory. Repository-root references such as
[`SPEC.md`](../SPEC.md) and [`README.md`](../README.md) live one level up.

## Foundations

- [`00-vision.md`](00-vision.md) — The problem, the one idea behind the gate, and the long-term vision.
- [`01-whitepaper.md`](01-whitepaper.md) — The motivating argument, design philosophy, and standard overview.
- [`02-srs.md`](02-srs.md) — Software requirements: functional and conformance requirements for `zp11/v1`.

## Design

- [`03-architecture.md`](03-architecture.md) — System architecture and the gate / zone / Proof-Pack component model.
- [`04-detailed-design.md`](04-detailed-design.md) — Module-level design of the gate pipeline and reference library.
- [`05-data-model.md`](05-data-model.md) — The Proof-Pack, receipt, evidence, and seal data model.
- [`06-api-cli-reference.md`](06-api-cli-reference.md) — Exhaustive `zp11` CLI and Python library reference, plus the `zp11.toml` reference.
- [`07-crypto-design.md`](07-crypto-design.md) — Canonicalisation, SHA-256 digests, Ed25519 receipts, and the signature chain.

## Security

- [`08-threat-model.md`](08-threat-model.md) — Adversaries, trust boundaries, and why the gate fails closed.
- [`09-security-architecture.md`](09-security-architecture.md) — The trust model, key handling, and threat analysis end to end.

## Testing & Conformance

- [`10-zones-reference.md`](10-zones-reference.md) — Per-zone normative reference for all eleven Zero-Point zones.
- [`11-policy-as-code.md`](11-policy-as-code.md) — Governance and ZP-8 policy conformance expressed declaratively.
- [`12-test-strategy.md`](12-test-strategy.md) — The test taxonomy, conformance suite, and test-vector methodology.
- [`13-conformance.md`](13-conformance.md) — Conformance criteria, the oracle, and the fail-closed merge decision.
- [`21-formal-model.md`](21-formal-model.md) — The formal model of the verification algorithm and gate semantics.

## Operations & Adoption

- [`14-cicd-integration.md`](14-cicd-integration.md) — Wiring `zp11 run` / `verify` as a required CI status check.
- [`15-operations-runbook.md`](15-operations-runbook.md) — Day-two operations, key custody, rotation, and incident handling.
- [`16-deployment.md`](16-deployment.md) — Deploying and operating the gate across environments.
- [`17-adoption-guide.md`](17-adoption-guide.md) — Mapping zones to existing checks and moving the gate to blocking.
- [`18-developer-guide.md`](18-developer-guide.md) — Contributing to and extending the reference implementation.
- [`19-user-guide.md`](19-user-guide.md) — End-to-end usage: install, keygen, configure, run, and verify.

## Reference

- [`20-related-work.md`](20-related-work.md) — How ZP-11 relates to neighbouring tools and prior art.
- [`22-glossary.md`](22-glossary.md) — Definitions of every term used across the documentation set.
- [`23-faq.md`](23-faq.md) — Frequently asked questions about the standard and the reference library.
- [`24-roadmap-adr.md`](24-roadmap-adr.md) — Roadmap and the architecture decision records.
