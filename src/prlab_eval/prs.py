from __future__ import annotations

from pathlib import Path

from prlab_eval.cases import ROOT, Case
from prlab_eval.github import GitHubError, gh_json, run
from prlab_eval.tools import TOOLS
from prlab_eval.tools.base import PullRequest, ReviewTool

WORKSPACE = ROOT.parent


def find_open_pr(repo: str, branch: str) -> PullRequest | None:
    rows = gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            branch,
            "--json",
            "url,number,headRefName",
            "--state",
            "open",
        ]
    ) or []
    if not rows:
        return None
    row = rows[0]
    return PullRequest(repo=repo, number=row["number"], url=row["url"], branch=branch)


def remote_branch_exists(local: Path, branch: str) -> bool:
    run(["git", "fetch", "origin", "--prune"], cwd=str(local))
    return bool(run(["git", "ls-remote", "--heads", "origin", branch], cwd=str(local)).strip())


def push_eval_branch(local: Path, branch: str) -> str:
    """Create the remote eval branch if it is missing. Force-update only when it already exists."""
    exists = remote_branch_exists(local, branch)
    cmd = ["git", "push", "-u", "origin", f"HEAD:{branch}"]
    if exists:
        cmd.append("--force-with-lease")
    run(cmd, cwd=str(local))
    return "updated" if exists else "created"


def context_files(case: Case, tool: ReviewTool | None, all_tools: bool) -> dict[str, str]:
    if all_tools:
        files: dict[str, str] = {}
        for registered in TOOLS.values():
            files.update(registered.context_files(case))
        return files
    if tool is None:
        return {}
    return tool.context_files(case)


def ensure_pr(
    case: Case,
    *,
    tool: ReviewTool | None = None,
    all_tools: bool = True,
    recreate: bool = False,
) -> PullRequest:
    existing = find_open_pr(case.github_repo, case.branch)
    if existing and not recreate:
        return existing

    local = WORKSPACE / case.local
    if not (local / ".git").exists():
        raise GitHubError(f"missing product clone: {local}")

    run(["git", "fetch", "origin", "--prune"], cwd=str(local))
    run(["git", "checkout", "-B", case.branch, "origin/main"], cwd=str(local))
    run(["git", "reset", "--hard", "origin/main"], cwd=str(local))
    run(["git", "apply", str(ROOT / case.patch)], cwd=str(local))

    for dest, content in context_files(case, tool, all_tools).items():
        path = local / dest
        path.write_text(content)
        run(["git", "add", dest], cwd=str(local))

    run(["git", "add", "-A"], cwd=str(local))
    status = run(["git", "status", "--porcelain"], cwd=str(local))
    if not status.strip():
        raise GitHubError(f"{case.id}: patch produced no changes")

    run(["git", "commit", "-m", f"{case.title}\n\n{case.body}"], cwd=str(local))
    push_eval_branch(local, case.branch)

    existing = find_open_pr(case.github_repo, case.branch)
    if existing:
        return existing

    url = run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            case.github_repo,
            "--base",
            "main",
            "--head",
            case.branch,
            "--title",
            case.title,
            "--body",
            case.body,
        ]
    ).strip()
    number = int(url.rsplit("/", 1)[-1])
    return PullRequest(repo=case.github_repo, number=number, url=url, branch=case.branch)


def close_pr(pr: PullRequest) -> None:
    try:
        run(["gh", "pr", "close", str(pr.number), "--repo", pr.repo, "--delete-branch"])
    except GitHubError as exc:
        text = str(exc).lower()
        if "already closed" not in text and "not found" not in text:
            raise
        try:
            run(["gh", "api", "-X", "DELETE", f"repos/{pr.repo}/git/refs/heads/{pr.branch}"])
        except GitHubError as delete_exc:
            delete_text = str(delete_exc).lower()
            if "404" not in delete_text and "not found" not in delete_text and "does not exist" not in delete_text:
                raise
