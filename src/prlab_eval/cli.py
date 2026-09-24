from __future__ import annotations

import argparse

from prlab_eval.cases import load_cases
from prlab_eval.cleanup import cleanup_eval
from prlab_eval.judge import LlmJudge, precheck_judge
from prlab_eval.prs import ensure_pr
from prlab_eval.tools import TOOLS, get_tool
from prlab_eval.trigger import trigger_case


def _wanted(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    return {item.strip() for item in raw.split(",") if item.strip()}


def _run_setup(only: str | None, tool_name: str | None) -> int:
    wanted = _wanted(only)
    tool = get_tool(tool_name) if tool_name else None
    for case in load_cases():
        if wanted and case.id not in wanted:
            continue
        pr = ensure_pr(case, tool=tool, all_tools=tool is None)
        print(f"{case.id}\t{case.intent}\t{pr.url}")
    return 0


def _run_trigger(tool_name: str, only: str | None) -> int:
    tool = get_tool(tool_name)
    wanted = _wanted(only)
    missing = 0
    for case in load_cases():
        if wanted and case.id not in wanted:
            continue
        status, pr = trigger_case(case, tool)
        url = pr.url if pr else "-"
        print(f"{case.id}\t{status}\t{url}")
        if status == "no_pr":
            missing += 1
    return 1 if missing else 0


def setup_prs(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open eval PRs. Does not trigger a review tool.")
    parser.add_argument("--only", help="comma-separated case ids")
    parser.add_argument(
        "--tool",
        help="select a review-tool plugin (default: every registered tool)",
    )
    args = parser.parse_args(argv)
    return _run_setup(args.only, args.tool)


def _run_cleanup(only: str | None) -> int:
    wanted = _wanted(only)
    for line in cleanup_eval(wanted):
        print(line)
    return 0


def _run_judge_check(provider: str | None, model: str | None) -> int:
    judge = LlmJudge.from_env(provider=provider, model=model)
    print(precheck_judge(judge))
    return 0


def cleanup_prs(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Close eval PRs and delete eval branches. Reports stay."
    )
    parser.add_argument("--only", help="comma-separated case ids")
    args = parser.parse_args(argv)
    return _run_cleanup(args.only)


def trigger_reviews(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ask a review tool to look at open eval PRs. Skips PRs that already have the mention."
    )
    parser.add_argument(
        "--tool",
        required=True,
        help=f"review tool to mention ({', '.join(sorted(TOOLS))})",
    )
    parser.add_argument("--only", help="comma-separated case ids")
    args = parser.parse_args(argv)
    return _run_trigger(args.tool, args.only)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PR review eval harness")
    sub = parser.add_subparsers(dest="command")

    setup_p = sub.add_parser("setup", help="open eval PRs")
    setup_p.add_argument("--only", help="comma-separated case ids")
    setup_p.add_argument("--tool", help="select a review-tool plugin")

    trigger_p = sub.add_parser(
        "trigger",
        help="mention a review tool on open eval PRs once",
    )
    trigger_p.add_argument(
        "--tool",
        required=True,
        help=f"review tool to mention ({', '.join(sorted(TOOLS))})",
    )
    trigger_p.add_argument("--only", help="comma-separated case ids")

    check_p = sub.add_parser("judge-check", help="verify the LLM judge before scoring")
    check_p.add_argument("--provider", dest="judge_provider")
    check_p.add_argument("--model", dest="judge_model")

    cleanup_p = sub.add_parser(
        "cleanup",
        help="close eval PRs and delete eval branches; reports stay",
    )
    cleanup_p.add_argument("--only", help="comma-separated case ids")

    args = parser.parse_args(argv)
    if args.command == "trigger":
        return _run_trigger(args.tool, args.only)
    if args.command == "setup":
        return _run_setup(args.only, args.tool)
    if args.command == "cleanup":
        return _run_cleanup(args.only)
    if args.command == "judge-check":
        return _run_judge_check(args.judge_provider, args.judge_model)
    return _run_setup(None, None)
