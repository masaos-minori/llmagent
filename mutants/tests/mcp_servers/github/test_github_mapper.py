"""tests/mcp_servers/github/test_github_mapper.py

Characterization tests for scripts/mcp_servers/github/mapper.py.

issue_to_info and pr_to_info have no existing test coverage (verified via
`rg issue_to_info|pr_to_info tests/` during the 04_refactor.md sweep of this
subsystem — only call sites in service_issues.py/service_pull_requests.py
exist, no direct or indirect test exercises the conversion logic itself).
These tests lock the exact field-by-field mapping from PyGithub-shaped
objects to IssueInfo/PullRequestInfo so any future change to this module is
a deliberate, visible decision.

Named test_github_mapper.py (not test_mapper.py) to avoid a pytest basename
collision with the pre-existing tests/agent/memory/test_mapper.py — neither
tests/agent/memory/ nor tests/mcp_servers/github/ has an __init__.py, so
pytest's rootdir-relative import mode requires unique basenames across the
whole tests/ tree.
"""

from __future__ import annotations

from types import SimpleNamespace

from mcp_servers.github.mapper import issue_to_info, pr_to_info


def _make_issue(**overrides: object) -> SimpleNamespace:
    """Build a minimal object satisfying mapper._IssueProtocol."""
    defaults: dict[str, object] = {
        "number": 42,
        "title": "Something broke",
        "state": "open",
        "html_url": "https://github.com/org/repo/issues/42",
        "body": "Steps to reproduce...",
        "created_at": SimpleNamespace(isoformat=lambda: "2026-01-01T00:00:00+00:00"),
        "updated_at": SimpleNamespace(isoformat=lambda: "2026-01-02T00:00:00+00:00"),
        "labels": [SimpleNamespace(name="bug"), SimpleNamespace(name="p1")],
        "assignees": [SimpleNamespace(login="alice"), SimpleNamespace(login="bob")],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_pull_request(**overrides: object) -> SimpleNamespace:
    """Build a minimal object satisfying mapper._PullRequestProtocol."""
    defaults: dict[str, object] = {
        "number": 7,
        "title": "Add feature",
        "state": "open",
        "html_url": "https://github.com/org/repo/pull/7",
        "body": "This PR adds a feature.",
        "head": SimpleNamespace(ref="feature-branch"),
        "base": SimpleNamespace(ref="main"),
        "created_at": SimpleNamespace(isoformat=lambda: "2026-01-03T00:00:00+00:00"),
        "updated_at": SimpleNamespace(isoformat=lambda: "2026-01-04T00:00:00+00:00"),
        "draft": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestIssueToInfo:
    """Lock the exact field mapping performed by issue_to_info."""

    def test_maps_all_scalar_fields(self) -> None:
        issue = _make_issue()
        info = issue_to_info(issue)

        assert info.number == 42
        assert info.title == "Something broke"
        assert info.state == "open"
        assert info.url == "https://github.com/org/repo/issues/42"
        assert info.body == "Steps to reproduce..."

    def test_maps_timestamps_via_isoformat(self) -> None:
        info = issue_to_info(_make_issue())

        assert info.created_at == "2026-01-01T00:00:00+00:00"
        assert info.updated_at == "2026-01-02T00:00:00+00:00"

    def test_maps_labels_to_name_list(self) -> None:
        info = issue_to_info(_make_issue())

        assert info.labels == ["bug", "p1"]

    def test_maps_assignees_to_login_list(self) -> None:
        info = issue_to_info(_make_issue())

        assert info.assignees == ["alice", "bob"]

    def test_preserves_none_body(self) -> None:
        info = issue_to_info(_make_issue(body=None))

        assert info.body is None

    def test_empty_labels_and_assignees_map_to_empty_lists(self) -> None:
        info = issue_to_info(_make_issue(labels=[], assignees=[]))

        assert info.labels == []
        assert info.assignees == []


class TestPrToInfo:
    """Lock the exact field mapping performed by pr_to_info."""

    def test_maps_all_scalar_fields(self) -> None:
        pr = _make_pull_request()
        info = pr_to_info(pr)

        assert info.number == 7
        assert info.title == "Add feature"
        assert info.state == "open"
        assert info.url == "https://github.com/org/repo/pull/7"
        assert info.body == "This PR adds a feature."
        assert info.draft is False

    def test_maps_head_and_base_ref(self) -> None:
        info = pr_to_info(_make_pull_request())

        assert info.head_ref == "feature-branch"
        assert info.base_ref == "main"

    def test_maps_timestamps_via_isoformat(self) -> None:
        info = pr_to_info(_make_pull_request())

        assert info.created_at == "2026-01-03T00:00:00+00:00"
        assert info.updated_at == "2026-01-04T00:00:00+00:00"

    def test_preserves_none_body(self) -> None:
        info = pr_to_info(_make_pull_request(body=None))

        assert info.body is None

    def test_maps_draft_true(self) -> None:
        info = pr_to_info(_make_pull_request(draft=True))

        assert info.draft is True
