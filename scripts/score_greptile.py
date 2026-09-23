#!/usr/bin/env python3
"""Pass/fail scorer for greptile-apps[bot] comments."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "cases" / "cases.json").read_text())
ALLOWED_LOGINS = {"greptile-apps[bot]"}


def run(args: list[str]) -> str:
    result = subprocess.run(args, check=True, text=True, capture_output=True)
    return result.stdout


def pr_number(repo: str, branch: str) -> int | None:
    rows = json.loads(
        run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repo,
                "--head",
                branch,
                "--json",
                "number,author",
                "--state",
                "all",
            ]
        )
        or "[]"
    )
    return rows[0]["number"] if rows else None


def collect(repo: str, number: int) -> tuple[str, set[str]]:
    issue = json.loads(
        run(["gh", "api", f"repos/{repo}/issues/{number}/comments"]) or "[]"
    )
    review = json.loads(
        run(["gh", "api", f"repos/{repo}/pulls/{number}/comments"]) or "[]"
    )
    reviews = json.loads(
        run(["gh", "api", f"repos/{repo}/pulls/{number}/reviews"]) or "[]"
    )
    texts: list[str] = []
    logins: set[str] = set()
    for row in list(issue) + list(review) + list(reviews):
        login = (row.get("user") or {}).get("login") or ""
        body = row.get("body") or ""
        if login:
            logins.add(login)
        if login == "greptile-apps[bot]":
            texts.append(body)
    return "\n".join(texts), logins


def matches(text: str, patterns: list[str]) -> bool:
    return all(re.search(pattern, text, re.I | re.S) for pattern in patterns)


def main() -> int:
    failed = 0
    print("id\ttest\tfinding\tisolation\tpr")
    for case in CASES:
        number = pr_number(case["github_repo"], case["branch"])
        if number is None:
            print(f"{case['id']}\t{case['test']}\tNO_PR\tNO_PR\t-")
            failed += 1
            continue
        text, logins = collect(case["github_repo"], number)
        trigger_only = {login for login in logins if login.endswith("[bot]") or login == "greptile-apps[bot]"}
        extras = sorted(login for login in logins if login not in ALLOWED_LOGINS and login.endswith("[bot]"))
        isolation = "PASS" if not extras else f"FAIL:{','.join(extras)}"
        finding = "PASS" if text and matches(text, case["must_flag"]) else "FAIL"
        if finding != "PASS" or isolation != "PASS":
            failed += 1
        print(
            f"{case['id']}\t{case['test']}\t{finding}\t{isolation}\thttps://github.com/{case['github_repo']}/pull/{number}"
        )
        _ = trigger_only
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
