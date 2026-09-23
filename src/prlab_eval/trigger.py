from __future__ import annotations

from prlab_eval.cases import Case
from prlab_eval.github import gh_api_list
from prlab_eval.prs import find_open_pr
from prlab_eval.tools.base import PullRequest, ReviewTool


def comment_has_trigger(bodies: list[str], trigger_body: str) -> bool:
    needle = trigger_body.strip().lower()
    if not needle:
        return False
    return any(needle in (body or "").lower() for body in bodies)


def issue_comment_bodies(pr: PullRequest) -> list[str]:
    rows = gh_api_list(f"repos/{pr.repo}/issues/{pr.number}/comments?per_page=100")
    return [row.get("body") or "" for row in rows]


def already_triggered(pr: PullRequest, tool: ReviewTool) -> bool:
    return comment_has_trigger(issue_comment_bodies(pr), tool.trigger_body)


def trigger_pr(pr: PullRequest, tool: ReviewTool) -> str:
    """Post the tool mention once. Returns triggered or skipped."""
    if already_triggered(pr, tool):
        return "skipped"
    tool.trigger(pr)
    return "triggered"


def trigger_case(case: Case, tool: ReviewTool) -> tuple[str, PullRequest | None]:
    pr = find_open_pr(case.github_repo, case.branch)
    if pr is None:
        return "no_pr", None
    return trigger_pr(pr, tool), pr
