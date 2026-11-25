# Contributing to ZP‑11

Thank you for helping improve the Zero‑Point Standard.

## Ground rules

- The gate is **fail‑closed**. Any change that could let a non‑`PASS` zone permit
  a merge will be rejected.
- Every change is gated by ZP‑11 itself (see `.github/workflows/ci.yml`). Your PR
  must produce a sealed `PASS` Proof‑Pack.
- Keep the reference implementation dependency‑light and the specification and
  code in agreement. If you change behavior, update `SPEC.md` in the same PR.

## Developer setup

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e . && pip install pytest
python -m pytest -q
python -m zp11.cli keygen --out ci.key && python -m zp11.cli run --key ci.key
```

## Pull requests

1. Fork and branch from `main`.
2. Add or update conformance tests for any behavior change.
3. Ensure `pytest` is green and the self‑gate seals.
4. Describe the change and link any relevant `SPEC.md` section.

## Design decisions

Architectural decisions are recorded under `docs/adr/`. Propose a new ADR for any
change to the pack format, the zone set, or the verification algorithm.

## Code of conduct

Be respectful and constructive. Harassment or discrimination of any kind is not
tolerated.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
