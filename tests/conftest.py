from __future__ import annotations

from pathlib import Path

import pytest

from prlab_eval.cases import load_cases
from prlab_eval.cleanup import cleanup_eval
from prlab_eval.harness import EvalResult, ReviewHarness
from prlab_eval.judge import JudgeConfigError, LlmJudge, TokenJudge, precheck_judge
from prlab_eval.report import terminal_summary, write_reports
from prlab_eval.tools import TOOLS, get_tool

REPORTS = Path(__file__).resolve().parents[1] / "reports"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("prlab")
    group.addoption(
        "--run-eval",
        action="store_true",
        help="run live GitHub review-tool tests",
    )
    group.addoption(
        "--tool",
        action="store",
        default=None,
        help=f"review tool to evaluate ({', '.join(sorted(TOOLS))})",
    )
    group.addoption(
        "--trigger",
        action="store_true",
        help="ask the selected tool to review during execute",
    )
    group.addoption(
        "--wait",
        action="store",
        type=int,
        default=0,
        help="seconds to poll for a review after execute",
    )
    group.addoption(
        "--cleanup",
        action="store_true",
        help="after writing reports, close eval PRs and delete eval branches",
    )
    group.addoption(
        "--allow-bots",
        action="store",
        default="",
        help="extra bot logins allowed for isolation (comma-separated)",
    )
    group.addoption(
        "--judge-provider",
        action="store",
        default=None,
        help="groq, gemini, ollama, github, or openai (auto-detected if omitted)",
    )
    group.addoption(
        "--judge-model",
        action="store",
        default=None,
        help="judge model (Groq: openai/gpt-oss-120b, qwen/qwen3.8-27b, or alias gpt-oss / qwen)",
    )
    group.addoption(
        "--fast",
        action="store_true",
        help="score claims by token match only; skip the LLM judge",
    )


def pytest_configure(config: pytest.Config) -> None:
    config._prlab_results = []  # type: ignore[attr-defined]
    if config.getoption("--run-eval"):
        config.option.verbose = max(int(getattr(config.option, "verbose", 0) or 0), 1)
        if not getattr(config.option, "htmlpath", None):
            REPORTS.mkdir(parents=True, exist_ok=True)
            config.option.htmlpath = str(REPORTS / "report.html")
            config.option.self_contained_html = True


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-eval"):
        if not config.getoption("--tool"):
            raise pytest.UsageError("--run-eval requires --tool")
        if config.getoption("--fast"):
            return
        try:
            LlmJudge.from_env(
                model=config.getoption("--judge-model"),
                provider=config.getoption("--judge-provider"),
            )
        except JudgeConfigError as exc:
            raise pytest.UsageError(str(exc)) from exc
        return
    skip = pytest.mark.skip(reason="opt in with --run-eval --tool NAME")
    for item in items:
        if "eval" in item.keywords:
            item.add_marker(skip)


def pytest_sessionstart(session: pytest.Session) -> None:
    if not session.config.getoption("--run-eval"):
        return
    if session.config.getoption("--fast"):
        print("fast judge: token match only, no LLM", flush=True)
        return
    judge = LlmJudge.from_env(
        model=session.config.getoption("--judge-model"),
        provider=session.config.getoption("--judge-provider"),
    )
    try:
        message = precheck_judge(judge)
    except JudgeConfigError as exc:
        pytest.exit(f"judge pre-check failed: {exc}", returncode=2)
    print(message, flush=True)


@pytest.fixture(scope="session")
def tool(request: pytest.FixtureRequest):
    name = request.config.getoption("--tool")
    if not name:
        pytest.skip("no --tool selected")
    return get_tool(name)


@pytest.fixture(scope="session")
def harness(tool, request: pytest.FixtureRequest) -> ReviewHarness:
    allow = {
        item.strip()
        for item in str(request.config.getoption("--allow-bots")).split(",")
        if item.strip()
    }
    fast = bool(request.config.getoption("--fast"))
    session = ReviewHarness(
        tool=tool,
        judge=TokenJudge()
        if fast
        else LlmJudge.from_env(
            model=request.config.getoption("--judge-model"),
            provider=request.config.getoption("--judge-provider"),
        ),
        trigger=bool(request.config.getoption("--trigger")),
        wait_seconds=int(request.config.getoption("--wait")),
        allow_bots=frozenset(allow),
        judge_mode="fast" if fast else "llm",
    )
    yield session


@pytest.fixture
def record_eval(request: pytest.FixtureRequest):
    def _record(result: EvalResult) -> EvalResult:
        request.config._prlab_results.append(result)  # type: ignore[attr-defined]
        return result

    return _record


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    results: list[EvalResult] = getattr(session.config, "_prlab_results", [])
    tool = session.config.getoption("--tool")
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if results and tool:
        path = write_reports(results, tool)
        if reporter:
            reporter.write_line(terminal_summary(results))
            reporter.write_line(f"eval report: {path}")
    if session.config.getoption("--run-eval") and session.config.getoption("--cleanup"):
        lines = cleanup_eval()
        if reporter:
            reporter.write_line(f"cleanup: {len(lines)} actions")
            for line in lines:
                reporter.write_line(line)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "case" in metafunc.fixturenames and metafunc.definition.get_closest_marker("eval"):
        cases = load_cases()
        metafunc.parametrize("case", cases, ids=[case.id for case in cases])
