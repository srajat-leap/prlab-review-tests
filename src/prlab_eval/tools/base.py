from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from prlab_eval.cases import Case
from prlab_eval.scoring import Review


@dataclass(frozen=True)
class PullRequest:
    repo: str
    number: int
    url: str
    branch: str


class ReviewTool(Protocol):
    """One PR-review product. Add a new module and register it in tools/__init__.py."""

    name: str
    bot_logins: frozenset[str]
    trigger_body: str

    def context_files(self, case: Case) -> dict[str, str]:
        """Repo files this tool needs on the PR (cluster config, etc.)."""

    def collect(self, pr: PullRequest) -> Review:
        """Return review text written by this tool's bot."""

    def trigger(self, pr: PullRequest) -> None:
        """Ask the tool to review. Runner account only."""
