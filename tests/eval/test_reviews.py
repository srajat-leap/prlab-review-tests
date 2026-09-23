from __future__ import annotations

import pytest

from prlab_eval.cases import Case
from prlab_eval.harness import ReviewHarness, failed_claims


@pytest.mark.eval
def test_review_tool_flags_regression(harness: ReviewHarness, case: Case, record_eval) -> None:
    # setup — open or reuse the eval PR
    pr = harness.setup(case)

    # execute — optional trigger + collect that tool's comments
    review = harness.execute(pr)

    # assert — every claim is asserted, and no unexpected review bots
    result = record_eval(harness.score(review, case))
    assert review.text, f"{harness.tool.name} left no review on {pr.url}"
    missed = failed_claims(result)
    assert not missed, (
        f"{harness.tool.name} missed {[item.claim_id + ': ' + item.reason for item in missed]} on {pr.url}"
    )
    assert result.isolation_passed, (
        f"unexpected bots {result.unexpected_bots} on {pr.url}"
    )

    # cleanup — optional; enabled with --cleanup on the session fixture
