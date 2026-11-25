"""Deterministic canonical serialization (RFC 8785, JSON Canonicalization Scheme).

A Proof-Pack is only re-runnable if two honest parties serialize the same data
to the same bytes. ``canonicalize`` implements the subset of RFC 8785 the
standard relies on: UTF-8, lexicographically sorted object keys, minimal
separators, no insignificant whitespace, and a rejection of values that have no
canonical form (NaN, Infinity, non-string keys). The output is stable across
Python versions and platforms, which is what makes a digest portable.
"""
from __future__ import annotations

import math
from typing import Any

__all__ = ["canonicalize", "CanonicalizationError"]


class CanonicalizationError(ValueError):
    """Raised when a value has no canonical JSON form."""


def _number(value: float | int) -> str:
    if isinstance(value, bool):  # bool is a subclass of int; handle upstream
        raise CanonicalizationError("bool is not a number")
    if isinstance(value, int):
        return str(value)
    if not math.isfinite(value):
        raise CanonicalizationError(f"non-finite number: {value!r}")
    if value == int(value) and abs(value) < 1e16:
        return str(int(value))
    # Shortest round-trippable form; repr() is shortest-round-trip in CPython.
    return repr(value)


def _string(value: str) -> str:
    out = ['"']
    for ch in value:
        code = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _encode(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, (int, float)):
        return _number(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_encode(v) for v in value) + "]"
    if isinstance(value, dict):
        items = []
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise CanonicalizationError("object keys must be strings")
            items.append(_string(key) + ":" + _encode(value[key]))
        return "{" + ",".join(items) + "}"
    raise CanonicalizationError(f"unserializable type: {type(value).__name__}")


def canonicalize(value: Any) -> bytes:
    """Return the canonical UTF-8 byte string for ``value`` (RFC 8785 subset)."""
    return _encode(value).encode("utf-8")
