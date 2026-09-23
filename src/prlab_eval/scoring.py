from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Finding:
    passed: bool
    missing: tuple[str, ...]
    matched: tuple[str, ...]


@dataclass(frozen=True)
class Isolation:
    passed: bool
    unexpected_bots: tuple[str, ...]


@dataclass
class Review:
    text: str
    logins: set[str] = field(default_factory=set)
    pr_url: str = ""
    comments: tuple[str, ...] = ()


def match_findings(text: str, patterns: tuple[str, ...] | list[str]) -> Finding:
    matched: list[str] = []
    missing: list[str] = []
    for pattern in patterns:
        flexible = pattern.replace("_", "[-_]")
        if text and re.search(flexible, text, flags=re.IGNORECASE | re.DOTALL):
            matched.append(pattern)
        else:
            missing.append(pattern)
    return Finding(passed=not missing and bool(text), missing=tuple(missing), matched=tuple(matched))


def check_isolation(logins: set[str], allowed_bots: set[str]) -> Isolation:
    unexpected = tuple(
        sorted(
            login
            for login in logins
            if login.endswith("[bot]") and login not in allowed_bots
        )
    )
    return Isolation(passed=not unexpected, unexpected_bots=unexpected)
