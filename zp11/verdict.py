"""Verdict semantics: absence of evidence is failure.

The entire standard turns on one asymmetry. A zone may return exactly two
verdicts, PASS or FAIL. Everything else a zone might do -- raise, time out,
return nothing, return something unparseable -- collapses to FAIL. There is no
third state that lets a change through, which is what "fail-closed, by
construction" means in code.
"""
from __future__ import annotations

import enum

__all__ = ["Verdict", "coerce"]


class Verdict(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"

    def __bool__(self) -> bool:  # Verdict.PASS is truthy, FAIL is falsy
        return self is Verdict.PASS


def coerce(value) -> Verdict:
    """Map anything a zone might produce onto PASS/FAIL; unknown -> FAIL."""
    if value is Verdict.PASS:
        return Verdict.PASS
    if isinstance(value, str) and value.strip().upper() == "PASS":
        return Verdict.PASS
    if value is True:
        return Verdict.PASS
    return Verdict.FAIL
