import pytest

from prlab_eval.cases import (
    capability_ids_for,
    load_capabilities,
    load_cases,
    resolve_capabilities,
)
from prlab_eval.tools import TOOLS


def test_cases_are_tool_agnostic() -> None:
    cases = load_cases()
    assert cases
    for case in cases:
        assert case.context in {"single-repo", "cluster"}
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


def test_capabilities_live_in_a_shared_catalog() -> None:
    catalog = load_capabilities()
    assert "cross-repo-downstream-impact" in catalog
    used = {item.id for case in load_cases() for item in case.capabilities}
    assert used <= set(catalog)


def test_case_can_reference_multiple_capability_ids() -> None:
    catalog = load_capabilities()
    ids = capability_ids_for(
        {"capabilities": ["public-contract-leak", "persist-leaked-envelope"]}
    )
    resolved = resolve_capabilities(ids, catalog, case_id="example")
    assert [item.id for item in resolved] == [
        "public-contract-leak",
        "persist-leaked-envelope",
    ]


def test_unknown_capability_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown capability"):
        resolve_capabilities(("not-a-skill",), load_capabilities(), case_id="example")
        assert "wicket" in case.tests.lower() or "leak" in case.tests.lower() or "protocol" in case.tests.lower()


def test_cluster_case_lists_sibling_repos() -> None:
    cluster = next(case for case in load_cases() if case.is_cluster)
    assert cluster.id == "test-protocol-omitted-confirm-counts-wicket-with-downstream-context"
    assert cluster.cluster_repos
    assert all("prlab-cricket-" in repo for repo in cluster.cluster_repos)


def test_single_repo_cases_have_no_cluster_repos() -> None:
    singles = [case for case in load_cases() if not case.is_cluster]
    assert singles
    assert all(case.cluster_repos == () for case in singles)


def test_every_case_has_a_claim() -> None:
    for case in load_cases():
        assert case.claims
        for claim in case.claims:
            assert claim.must_assert
            assert claim.id


def test_cluster_case_has_a_downstream_claim() -> None:
    cluster = next(case for case in load_cases() if case.is_cluster)
    ids = {claim.id for claim in cluster.claims}
    assert "names-downstream-consumer" in ids
