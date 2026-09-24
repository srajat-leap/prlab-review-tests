import pytest

from prlab_eval.cases import (
    capability_ids_for,
    load_capabilities,
    load_cases,
    resolve_capabilities,
)
from prlab_eval.tools import TOOLS


def test_cases_are_shared_across_tools() -> None:
    cases = load_cases()
    assert cases
    for case in cases:
        dumped = case.__dict__
        joined = " ".join(str(value) for value in dumped.values())
        for tool_name in TOOLS:
            assert tool_name not in case.id
            assert f"{tool_name}-" not in joined


def test_case_ids_start_with_test_and_describe_intent() -> None:
    for case in load_cases():
        assert case.id.startswith("test-")
        assert case.intent
        assert case.tests
        assert case.capability.id
        assert case.capability.name
        assert case.capability.asks.endswith("?")
        assert case.capabilities[0] is case.capability
        assert "wicket" in case.tests.lower() or "leak" in case.tests.lower() or "protocol" in case.tests.lower()


def test_capabilities_live_in_a_shared_catalog() -> None:
    catalog = load_capabilities()
    assert "cross-repo-impact" in catalog
    used = {item.id for case in load_cases() for item in case.capabilities}
    assert used <= set(catalog)
    joined = " ".join(f"{item.id} {item.name} {item.asks}" for item in catalog.values()).lower()
    assert "law of demeter" not in joined
    assert "law-of-demeter" not in joined


def test_case_can_reference_multiple_capability_ids() -> None:
    catalog = load_capabilities()
    ids = capability_ids_for(
        {"capabilities": ["contract-leak", "leak-propagation"]}
    )
    resolved = resolve_capabilities(ids, catalog, case_id="example")
    assert [item.id for item in resolved] == [
        "contract-leak",
        "leak-propagation",
    ]


def test_unknown_capability_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown capability"):
        resolve_capabilities(("not-a-skill",), load_capabilities(), case_id="example")


def test_every_case_has_a_claim() -> None:
    for case in load_cases():
        assert case.claims
        for claim in case.claims:
            assert claim.must_assert
            assert claim.id


def test_downstream_case_names_a_consumer() -> None:
    case = next(
        item
        for item in load_cases()
        if item.id == "test-protocol-omitted-confirm-counts-wicket-with-downstream-context"
    )
    ids = {claim.id for claim in case.claims}
    assert "names-downstream-consumer" in ids
