from prlab_eval.harness import EvalResult
from prlab_eval.judge import ClaimVerdict
from prlab_eval.report import isolation_label, terminal_summary, write_reports


def test_write_reports_separates_comment_from_judge(tmp_path) -> None:
    results = [
        EvalResult(
            case_id="stats-count-not-out",
            context="single-repo",
            tool="greptile",
            pr_url="https://example.test/pr/2",
            finding_passed=True,
            isolation_passed=True,
            claims=[
                ClaimVerdict(
                    claim_id="not-out-counted-as-wicket",
                    must_assert="NOT_OUT should not increment wickets.",
                    passed=True,
                    quote="NOT_OUT should not increment the wicket total.",
                    reason="asserted",
                    tokens_expected=("NOT_OUT", "wicket"),
                    tokens_matched=("NOT_OUT", "wicket"),
                    tokens_missing=(),
                )
            ],
            actual="NOT_OUT should not increment the wicket total.",
            comments=["NOT_OUT should not increment the wicket total."],
        ),
        EvalResult(
            case_id="social-post-appeals",
            context="single-repo",
            tool="greptile",
            pr_url="https://example.test/pr/3",
            finding_passed=False,
            isolation_passed=True,
            claims=[
                ClaimVerdict(
                    claim_id="appeal-posted-as-wicket",
                    must_assert="Posting WICKET for kind=appeal treats an appeal as a wicket.",
                    passed=False,
                    quote="",
                    reason="not asserted",
                    tokens_expected=("appeal", "WICKET"),
                    tokens_matched=("WICKET",),
                    tokens_missing=("appeal",),
                )
            ],
            actual="This posts WICKET for every clip.",
            comments=["This posts WICKET for every clip.", "README is stale."],
        ),
    ]
    latest = write_reports(results, "greptile", out_dir=tmp_path)
    text = latest.read_text()
    assert "Expected finding" in text
    assert "Actual PR comment" in text
    assert "Judge verdict" in text
    assert "Judge evidence" in text
    assert "NOT_OUT should not increment wickets." in text
    assert "This posts WICKET for every clip." in text
    assert "Precision" in text
    assert "Recall" in text
    assert "not asserted" in text
    assert isolation_label(results[0]) == "yes"
    payload = (tmp_path / "latest.json").read_text()
    assert '"precision"' in payload
    assert '"recall"' in payload
    assert '"must_assert"' in payload
    table = terminal_summary(results)
    assert "stats-count-not-out" in table
    assert "P=" in table
    assert "R=" in table
