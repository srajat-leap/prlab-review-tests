from prlab_eval.cases import Claim
from prlab_eval.judge import verdict_for
from prlab_eval.metrics import aggregate_metrics, pct, score_metrics


def test_perfect_precision_and_recall() -> None:
    review = "Omitting umpire_confirmed counts a wicket."
    claim = Claim(id="x", must_assert="Omitted confirmation counts a wicket.", tokens=("wicket",))
    verdict = verdict_for(claim, review, asserts=True, quote="Omitting umpire_confirmed counts a wicket.", reason="ok")
    metrics = score_metrics([verdict], [review])
    assert metrics.precision == 1
    assert metrics.recall == 1
    assert metrics.f1 == 1
    assert metrics.false_positives == 0


def test_extra_comment_lowers_precision() -> None:
    hit = "Omitting umpire_confirmed counts a wicket."
    extra = "Please update the README while you are here."
    claim = Claim(id="x", must_assert="Omitted confirmation counts a wicket.", tokens=("wicket",))
    verdict = verdict_for(claim, hit, asserts=True, quote="Omitting umpire_confirmed counts a wicket.", reason="ok")
    metrics = score_metrics([verdict], [hit, extra])
    assert metrics.recall == 1
    assert metrics.precision == 0.5
    assert metrics.false_positives == 1


def test_missed_claim_is_zero_recall() -> None:
    extra = "Please update the README while you are here."
    claim = Claim(id="x", must_assert="Omitted confirmation counts a wicket.", tokens=("wicket",))
    verdict = verdict_for(claim, extra, asserts=False, quote="", reason="not asserted")
    metrics = score_metrics([verdict], [extra])
    assert metrics.recall == 0
    assert metrics.precision == 0
    assert metrics.false_negatives == 1


def test_aggregate_is_micro_averaged() -> None:
    hit = score_metrics(
        [
            verdict_for(
                Claim(id="a", must_assert="A", tokens=()),
                "found it",
                asserts=True,
                quote="found it",
                reason="ok",
            )
        ],
        ["found it"],
    )
    miss = score_metrics(
        [
            verdict_for(
                Claim(id="b", must_assert="B", tokens=()),
                "docs only",
                asserts=False,
                quote="",
                reason="no",
            )
        ],
        ["docs only", "more docs"],
    )
    overall = aggregate_metrics([hit, miss])
    assert overall.true_positives == 1
    assert overall.false_negatives == 1
    assert overall.recall == 0.5
    assert overall.comments == 3
    assert overall.relevant_comments == 1
    assert overall.precision == 1 / 3


def test_pct_formats_percent() -> None:
    assert pct(0.5) == "50%"
    assert pct(1) == "100%"
    assert pct(0) == "0%"
