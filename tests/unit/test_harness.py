from prlab_eval.cases import load_cases
from prlab_eval.harness import ReviewHarness
from prlab_eval.judge import CallableJudge
from prlab_eval.scoring import Review
from prlab_eval.tools.greptile import GreptileTool


def _pass_if_text_mentions(word: str):
    def decide(claim, review_text: str):
        visible = review_text
        if word.lower() in visible.lower():
            start = visible.lower().index(word.lower())
            quote = visible[start : start + len(word)]
            return True, quote, "asserted"
        return False, "", "not asserted"

    return decide


def test_score_passes_when_judge_accepts_the_claim() -> None:
    case = next(item for item in load_cases() if item.id == "stats-count-not-out")
    harness = ReviewHarness(
        tool=GreptileTool(),
        judge=CallableJudge(_pass_if_text_mentions("NOT_OUT")),
    )
    review = Review(
        text="NOT_OUT should not increment the wicket total.",
        logins={"greptile-apps[bot]"},
        pr_url="https://example.test/pr/1",
    )
    result = harness.score(review, case)
    assert result.finding_passed
    assert result.isolation_passed
    assert result.claims[0].passed
    assert result.claims[0].quote
    assert result.actual
    assert result.comments
    assert result.metrics.recall == 1
    assert result.context == "single-repo"


def test_score_fails_when_review_does_not_assert_the_claim() -> None:
    case = next(item for item in load_cases() if item.id == "stats-count-not-out")
    harness = ReviewHarness(
        tool=GreptileTool(),
        judge=CallableJudge(_pass_if_text_mentions("NOT_OUT")),
    )
    review = Review(
        text="The wicket documentation is slightly stale.",
        logins={"greptile-apps[bot]"},
        pr_url="https://example.test/pr/1",
    )
    result = harness.score(review, case)
    assert not result.finding_passed
    assert result.claims[0].reason == "not asserted"


def test_score_fails_isolation_for_other_bots() -> None:
    case = load_cases()[0]
    harness = ReviewHarness(
        tool=GreptileTool(),
        judge=CallableJudge(_pass_if_text_mentions("umpire_confirmed")),
    )
    review = Review(
        text="umpire_confirmed omitted default becomes a wicket",
        logins={"greptile-apps[bot]", "cursor[bot]"},
        pr_url="https://example.test/pr/1",
    )
    result = harness.score(review, case)
    assert result.finding_passed
    assert not result.isolation_passed
    assert result.unexpected_bots == ("cursor[bot]",)
