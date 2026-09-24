from pathlib import Path

from prlab_eval.cleanup import leftover_eval_prs, reset_local_clone, try_run
from prlab_eval.github import GitHubError
from prlab_eval.tools.base import PullRequest


def test_try_run_swallows_already_gone(monkeypatch) -> None:
    def boom(_args, cwd=None):
        raise GitHubError("gh api failed: HTTP 404: Not Found")

    monkeypatch.setattr("prlab_eval.cleanup.run", boom)
    assert try_run(["gh", "api", "-X", "DELETE", "repos/x/y/git/refs/heads/eval/z"]) is False


def test_try_run_raises_real_errors(monkeypatch) -> None:
    def boom(_args, cwd=None):
        raise GitHubError("gh failed: HTTP 401: Bad credentials")

    monkeypatch.setattr("prlab_eval.cleanup.run", boom)
    try:
        try_run(["gh", "auth", "status"])
    except GitHubError as exc:
        assert "401" in str(exc)
    else:
        raise AssertionError("expected GitHubError")


def test_leftover_eval_prs_skips_known_case_branches(monkeypatch) -> None:
    from prlab_eval.cases import load_cases

    cases = load_cases()
    first = cases[0]

    def fake_list(repo: str) -> list[PullRequest]:
        if repo != first.github_repo:
            return []
        return [
            PullRequest(repo=repo, number=1, url="https://example.test/1", branch=first.branch),
            PullRequest(repo=repo, number=99, url="https://example.test/99", branch="eval/old-trap"),
        ]

    monkeypatch.setattr("prlab_eval.cleanup.list_open_eval_prs", fake_list)
    extras = leftover_eval_prs(cases)
    assert [pr.branch for pr in extras] == ["eval/old-trap"]


def test_reset_local_clone_skips_missing_repo(tmp_path: Path) -> None:
    reset_local_clone(tmp_path / "no-such-clone", {"eval/x"})
