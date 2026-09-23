from prlab_eval.scoring import Review, check_isolation, match_findings


def test_match_findings_requires_every_pattern() -> None:
    text = "Omitted umpire_confirmed defaults to true and counts a wicket."
    finding = match_findings(text, ("umpire_confirmed", "(omitted|default|missing)", "wicket"))
    assert finding.passed
    assert finding.missing == ()


def test_match_findings_reports_missing_pattern() -> None:
    finding = match_findings("raw_ball debug field", ("raw_ball", "protocol"))
    assert not finding.passed
    assert finding.missing == ("protocol",)
    assert finding.matched == ("raw_ball",)


def test_match_findings_treats_hyphen_like_underscore() -> None:
    finding = match_findings("the new raw-ball behavior", ("raw_ball",))
    assert finding.passed
    assert finding.matched == ("raw_ball",)


def test_empty_review_fails() -> None:
    finding = match_findings("", ("wicket",))
    assert not finding.passed
    assert finding.missing == ("wicket",)


def test_isolation_allows_selected_bot_and_humans() -> None:
    isolation = check_isolation(
        {"greptile-apps[bot]", "srajat-leap"},
        {"greptile-apps[bot]"},
    )
    assert isolation.passed
    assert isolation.unexpected_bots == ()


def test_isolation_flags_other_review_bots() -> None:
    isolation = check_isolation(
        {"greptile-apps[bot]", "cursor[bot]"},
        {"greptile-apps[bot]"},
    )
    assert not isolation.passed
    assert isolation.unexpected_bots == ("cursor[bot]",)


def test_review_dataclass_defaults() -> None:
    review = Review(text="")
    assert review.logins == set()
    assert review.pr_url == ""
    assert review.comments == ()
