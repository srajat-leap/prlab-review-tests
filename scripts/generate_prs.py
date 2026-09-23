#!/usr/bin/env python3
"""Open eval PRs from cases.json. Does not mention review bots unless asked."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
CASES = json.loads((ROOT / "cases" / "cases.json").read_text())


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=check, text=True, capture_output=True)


def existing_pr(repo: str, branch: str) -> str | None:
    listed = run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            branch,
            "--json",
            "url",
            "--state",
            "open",
        ]
    )
    rows = json.loads(listed.stdout or "[]")
    return rows[0]["url"] if rows else None


def apply_case(case: dict, trigger: bool) -> str:
    local = WORKSPACE / case["local"]
    if not (local / ".git").exists():
        raise SystemExit(f"missing product clone: {local}")

    run(["git", "fetch", "origin"], cwd=local)
    run(["git", "checkout", "-B", case["branch"], "origin/main"], cwd=local)
    run(["git", "reset", "--hard", "origin/main"], cwd=local)

    patch = ROOT / case["patch"]
    applied = run(["git", "apply", str(patch)], cwd=local, check=False)
    if applied.returncode != 0:
        raise SystemExit(f"{case['id']}: patch failed\n{applied.stderr}")

    for dest, src in case.get("extra_files", {}).items():
        shutil.copy(ROOT / src, local / dest)
        run(["git", "add", dest], cwd=local)

    run(["git", "add", "-A"], cwd=local)
    status = run(["git", "status", "--porcelain"], cwd=local)
    if not status.stdout.strip():
        raise SystemExit(f"{case['id']}: patch produced no changes")

    run(
        [
            "git",
            "commit",
            "-m",
            f"{case['title']}\n\n{case['body']}",
        ],
        cwd=local,
    )
    run(["git", "push", "-u", "origin", f"HEAD:{case['branch']}", "--force-with-lease"], cwd=local)

    url = existing_pr(case["github_repo"], case["branch"])
    if url is None:
        created = run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                case["github_repo"],
                "--base",
                "main",
                "--head",
                case["branch"],
                "--title",
                case["title"],
                "--body",
                case["body"],
            ]
        )
        url = created.stdout.strip()

    if trigger:
        run(
            [
                "gh",
                "pr",
                "comment",
                url,
                "--body",
                "@greptileai",
            ]
        )
    return url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger-greptile", action="store_true")
    parser.add_argument("--only", help="comma-separated case ids")
    args = parser.parse_args()
    wanted = {item.strip() for item in args.only.split(",")} if args.only else None

    urls: list[str] = []
    for case in CASES:
        if wanted and case["id"] not in wanted:
            continue
        url = apply_case(case, trigger=args.trigger_greptile)
        print(f"{case['id']}\t{case['test']}\t{url}")
        urls.append(url)
    if not urls:
        print("no cases selected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
