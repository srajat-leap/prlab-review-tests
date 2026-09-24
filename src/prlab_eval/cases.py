from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "cases" / "cases.json"
CAPABILITIES_PATH = ROOT / "cases" / "capabilities.json"


@dataclass(frozen=True)
class Claim:
    id: str
    must_assert: str
    tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    asks: str


@dataclass(frozen=True)
class Case:
    id: str
    intent: str
    tests: str
    capabilities: tuple[Capability, ...]
    github_repo: str
    local: str
    patch: str
    branch: str
    title: str
    body: str
    claims: tuple[Claim, ...]

    @property
    def capability(self) -> Capability:
        return self.capabilities[0]


def _parse_claim(row: dict) -> Claim:
    return Claim(
        id=row["id"],
        must_assert=row["must_assert"],
        tokens=tuple(row.get("tokens") or ()),
    )


def load_capabilities(path: Path | None = None) -> dict[str, Capability]:
    raw = json.loads((path or CAPABILITIES_PATH).read_text())
    catalog: dict[str, Capability] = {}
    for cap_id, spec in raw.items():
        name = (spec.get("name") or "").strip()
        asks = (spec.get("asks") or "").strip()
        if not name or not asks:
            raise ValueError(f"capability {cap_id} needs name and asks")
        catalog[cap_id] = Capability(id=cap_id, name=name, asks=asks)
    if not catalog:
        raise ValueError("capabilities catalog is empty")
    return catalog


def capability_ids_for(row: dict) -> tuple[str, ...]:
    if "capabilities" in row:
        values = row["capabilities"]
        if isinstance(values, str):
            return (values,)
        return tuple(str(item) for item in values)
    value = row.get("capability")
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    if isinstance(value, dict) and value.get("id"):
        return (str(value["id"]),)
    return ()


def resolve_capabilities(
    ids: tuple[str, ...],
    catalog: dict[str, Capability],
    *,
    case_id: str,
) -> tuple[Capability, ...]:
    if not ids:
        raise ValueError(f"{case_id} needs capability or capabilities")
    resolved = []
    for cap_id in ids:
        try:
            resolved.append(catalog[cap_id])
        except KeyError as exc:
            known = ", ".join(sorted(catalog))
            raise ValueError(f"{case_id} unknown capability {cap_id!r}. known: {known}") from exc
    return tuple(resolved)


def load_cases(path: Path | None = None) -> list[Case]:
    catalog = load_capabilities()
    raw = json.loads((path or CASES_PATH).read_text())
    cases = []
    for row in raw:
        claims = tuple(_parse_claim(item) for item in row["claims"])
        case_id = row["id"]
        if not case_id.startswith("test-"):
            raise ValueError(f"{case_id} must start with 'test-'")
        if not claims:
            raise ValueError(f"{case_id} has no claims")
        intent = (row.get("intent") or "").strip()
        tests = (row.get("tests") or "").strip()
        if not intent or not tests:
            raise ValueError(f"{case_id} needs intent and tests")
        capabilities = resolve_capabilities(capability_ids_for(row), catalog, case_id=case_id)
        cases.append(
            Case(
                id=case_id,
                intent=intent,
                tests=tests,
                capabilities=capabilities,
                github_repo=row["github_repo"],
                local=row["local"],
                patch=row["patch"],
                branch=row["branch"],
                title=row["title"],
                body=row["body"],
                claims=claims,
            )
        )
    return cases
