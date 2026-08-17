"""tests/mcp_servers/github/test_service_business.py

Characterization tests for scripts/mcp_servers/github/service_business.py.

`GitHubService._fmt_issue_line` and `_fmt_pr_line` are used by
service_dispatch.py's list/search formatting methods but are never exercised
by the existing test suite (verified via `rg list_issues|list_pull_requests`
against tests/mcp_servers/github/ during the 04_refactor.md sweep of this
subsystem; baseline coverage was 79%, missing lines 44-45 and 50-51 — the
bodies of both static methods). These tests lock the exact, verbatim string
output of both formatters, including both branches of each conditional
(labels present/absent, draft true/false), before any refactor.
"""

from __future__ import annotations

from mcp_servers.github.models_base import IssueInfo, PullRequestInfo
from mcp_servers.github.service_dispatch import GitHubService


def _make_issue(**overrides: object) -> IssueInfo:
    defaults: dict[str, object] = {
        "number": 42,
        "title": "Fix the thing",
        "state": "open",
        "url": "https://github.com/example/repo/issues/42",
        "body": None,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "labels": [],
        "assignees": [],
    }
    defaults.update(overrides)
    return IssueInfo(**defaults)  # type: ignore[arg-type]  # — dict values widened for **overrides; fields are valid at runtime


def _make_pr(**overrides: object) -> PullRequestInfo:
    defaults: dict[str, object] = {
        "number": 7,
        "title": "Add feature",
        "state": "open",
        "url": "https://github.com/example/repo/pull/7",
        "body": None,
        "head_ref": "feature-branch",
        "base_ref": "main",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "draft": False,
    }
    defaults.update(overrides)
    return PullRequestInfo(**defaults)  # type: ignore[arg-type]  # — dict values widened for **overrides; fields are valid at runtime


class TestFmtIssueLine:
    """Lock the exact formatting behavior of GitHubService._fmt_issue_line."""

    def test_issue_without_labels_omits_labels_segment(self) -> None:
        """No 'labels=[...]' segment appears when the issue has no labels."""
        issue = _make_issue(labels=[])

        result = GitHubService._fmt_issue_line(issue)

        assert result == (
            "#42 [open] Fix the thing\nhttps://github.com/example/repo/issues/42"
        )

    def test_issue_with_labels_includes_labels_segment(self) -> None:
        """The 'labels=[...]' segment is joined with ', ' and placed before the title."""
        issue = _make_issue(labels=["bug", "priority-high"])

        result = GitHubService._fmt_issue_line(issue)

        assert result == (
            "#42 [open] labels=[bug, priority-high] Fix the thing\n"
            "https://github.com/example/repo/issues/42"
        )

    def test_issue_with_single_label(self) -> None:
        """A single-element labels list renders without a separator."""
        issue = _make_issue(number=1, state="closed", labels=["wontfix"], title="X")

        result = GitHubService._fmt_issue_line(issue)

        assert result == f"#1 [closed] labels=[wontfix] X\n{issue.url}"


class TestFmtPrLine:
    """Lock the exact formatting behavior of GitHubService._fmt_pr_line."""

    def test_non_draft_pr_omits_draft_segment(self) -> None:
        """No '[draft]' marker appears for a non-draft pull request."""
        pr = _make_pr(draft=False)

        result = GitHubService._fmt_pr_line(pr)

        assert result == (
            "#7 [open] Add feature (feature-branch->main)\n"
            "https://github.com/example/repo/pull/7"
        )

    def test_draft_pr_includes_draft_segment(self) -> None:
        """The ' [draft]' marker is inserted immediately after the state bracket."""
        pr = _make_pr(draft=True)

        result = GitHubService._fmt_pr_line(pr)

        assert result == (
            "#7 [open] [draft] Add feature (feature-branch->main)\n"
            "https://github.com/example/repo/pull/7"
        )

    def test_pr_head_and_base_ref_order(self) -> None:
        """head_ref appears before base_ref, joined with '->'."""
        pr = _make_pr(head_ref="dev", base_ref="release", draft=False)

        result = GitHubService._fmt_pr_line(pr)

        assert "(dev->release)" in result
