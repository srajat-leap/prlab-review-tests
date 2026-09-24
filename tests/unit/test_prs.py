from pathlib import Path

from prlab_eval.prs import push_eval_branch, remote_branch_exists


def test_remote_branch_exists_is_false_when_ls_remote_is_empty(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(args, cwd=None):
        calls.append(list(args))
        return ""

    monkeypatch.setattr("prlab_eval.prs.run", fake_run)
    assert remote_branch_exists(tmp_path, "eval/missing") is False
    assert calls[0][:3] == ["git", "fetch", "origin"]
    assert "--prune" in calls[0]
    assert calls[1] == ["git", "ls-remote", "--heads", "origin", "eval/missing"]


def test_push_creates_branch_when_missing(monkeypatch, tmp_path: Path) -> None:
    pushed: list[list[str]] = []

    def fake_run(args, cwd=None):
        if args[:2] == ["git", "push"]:
            pushed.append(list(args))
        return ""

    monkeypatch.setattr("prlab_eval.prs.run", fake_run)
    assert push_eval_branch(tmp_path, "eval/new") == "created"
    assert pushed == [["git", "push", "-u", "origin", "HEAD:eval/new"]]


def test_push_force_updates_existing_branch(monkeypatch, tmp_path: Path) -> None:
    pushed: list[list[str]] = []

    def fake_run(args, cwd=None):
        if args[:3] == ["git", "ls-remote", "--heads"]:
            return "abc123\trefs/heads/eval/old"
        if args[:2] == ["git", "push"]:
            pushed.append(list(args))
        return ""

    monkeypatch.setattr("prlab_eval.prs.run", fake_run)
    assert push_eval_branch(tmp_path, "eval/old") == "updated"
    assert pushed == [["git", "push", "-u", "origin", "HEAD:eval/old", "--force-with-lease"]]
