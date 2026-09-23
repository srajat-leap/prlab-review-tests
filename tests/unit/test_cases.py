from prlab_eval.cases import load_cases
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


def test_cluster_case_lists_sibling_repos() -> None:
    cluster = next(case for case in load_cases() if case.is_cluster)
    assert cluster.id == "protocol-default-confirm-cluster"
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
