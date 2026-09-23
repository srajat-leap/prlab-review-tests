import json

from prlab_eval.cases import load_cases
from prlab_eval.github import parse_json_pages
from prlab_eval.tools.base import PullRequest
from prlab_eval.tools.greptile import GreptileTool, comment_text


def test_greptile_writes_cluster_file_only_for_cluster_cases() -> None:
    tool = GreptileTool()
    cases = {case.id: case for case in load_cases()}
    assert tool.context_files(cases["protocol-default-confirm-cold"]) == {}
    files = tool.context_files(cases["protocol-default-confirm-cluster"])
    assert set(files) == {"greptile.json"}
    payload = json.loads(files["greptile.json"])
    assert payload["context"]["repos"] == list(cases["protocol-default-confirm-cluster"].cluster_repos)


def test_registered_tools_expose_bots_and_trigger() -> None:
    tool = GreptileTool()
    assert tool.name == "greptile"
    assert tool.bot_logins
    assert tool.trigger_body


def test_comment_text_keeps_inline_path() -> None:
    text = comment_text(
        {"body": "**Missing Confirmation Becomes Wicket**", "path": "src/animator.js", "line": 11}
    )
    assert text.startswith("src/animator.js:11")
    assert "Missing Confirmation" in text


def test_parse_json_pages_joins_concatenated_arrays() -> None:
    pages = parse_json_pages('[{"id": 1}][{"id": 2}]')
    assert [row["id"] for row in pages] == [1, 2]


def test_collect_joins_paginated_bot_comments(monkeypatch) -> None:
    def fake_list(path: str):
        if "issues" in path:
            return [{"user": {"login": "srajat-leap"}, "body": "@greptileai"}]
        if "/reviews" in path:
            return [{"user": {"login": "greptile-apps[bot]"}, "body": "", "state": "COMMENTED"}]
        return [
            {
                "user": {"login": "greptile-apps[bot]"},
                "path": "src/animator.js",
                "line": 11,
                "body": "<p>When a raw wicket omits `umpire_confirmed`.</p>",
            }
        ]

    monkeypatch.setattr("prlab_eval.tools.greptile.gh_api_list", fake_list)
    review = GreptileTool().collect(
        PullRequest(repo="srajat-leap/prlab-cricket-broadcast", number=3, url="https://example.test/3", branch="eval/x")
    )
    assert "src/animator.js:11" in review.text
    assert "umpire_confirmed" in review.text
    assert review.comments
    assert "srajat-leap" in review.logins
