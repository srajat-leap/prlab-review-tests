from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "cases" / "cases.json"


@dataclass(frozen=True)
class Claim:
    id: str
    must_assert: str
    tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class Case:
    id: str
    context: str
    github_repo: str
    local: str
    patch: str
    branch: str
    title: str
    body: str
    claims: tuple[Claim, ...]
    cluster_repos: tuple[str, ...] = ()

    @property
    def is_cluster(self) -> bool:
        return self.context == "cluster"


def _parse_claim(row: dict) -> Claim:
    return Claim(
        id=row["id"],
        must_assert=row["must_assert"],
        tokens=tuple(row.get("tokens") or ()),
    )


def load_cases(path: Path | None = None) -> list[Case]:
    raw = json.loads((path or CASES_PATH).read_text())
    cases = []
    for row in raw:
        claims = tuple(_parse_claim(item) for item in row["claims"])
        if not claims:
            raise ValueError(f"{row['id']} has no claims")
        cases.append(
            Case(
                id=row["id"],
                context=row["context"],
                github_repo=row["github_repo"],
                local=row["local"],
                patch=row["patch"],
                branch=row["branch"],
                title=row["title"],
                body=row["body"],
                claims=claims,
                cluster_repos=tuple(row.get("cluster_repos") or ()),
            )
        )
    return cases
