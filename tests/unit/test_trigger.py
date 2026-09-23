from prlab_eval.trigger import comment_has_trigger


def test_detects_exact_mention() -> None:
    assert comment_has_trigger(["@greptileai"], "@greptileai")


def test_detects_mention_in_longer_comment() -> None:
    assert comment_has_trigger(["please look at this\n@greptileai\n"], "@greptileai")


def test_is_case_insensitive() -> None:
    assert comment_has_trigger(["@GreptileAI"], "@greptileai")


def test_missing_mention_is_false() -> None:
    assert not comment_has_trigger(["looks good", ""], "@greptileai")


def test_empty_trigger_never_matches() -> None:
    assert not comment_has_trigger(["@greptileai"], "  ")
