# Security Policy

ZP‑11 is security‑critical by design: it decides whether a change may reach
`main`. We take reports seriously.

## Reporting a vulnerability

Please report suspected vulnerabilities privately via GitHub Security Advisories
on this repository (**Security → Report a vulnerability**). Do **not** open a
public issue for a security report.

Include, where possible: a description, affected version/commit, reproduction
steps, and impact. We aim to acknowledge within a few business days.

## Scope

In scope:

- Forging a sealed `PASS` Proof‑Pack without the signing key.
- Causing a `FAIL` or silent zone to be accepted as merge‑permitted.
- Canonicalization or signature‑verification bypasses.
- Evidence tampering that is not detected by `verify`.

Out of scope:

- Misconfiguration of zones in a downstream `zp11.toml`.
- Weaknesses in third‑party tools a zone wraps.
- The secrecy of signing keys stored by an adopter.

## Trust model

The signing key is the root of trust and must be stored outside the gated
repository. ZP‑10 (independent re‑run) is the control against a compromised
primary runner; keep the two runners isolated.
