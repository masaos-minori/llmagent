"""mcp_servers/github/mapper.py

Mapper functions: convert PyGithub objects to Pydantic response models.

Extracted from service.py to separate conversion responsibility from business logic.
"""

from typing import Protocol

from mcp_servers.github.models import IssueInfo, PullRequestInfo


class _LabelProtocol(Protocol):
    """Protocol for PyGithub Label objects."""

    name: str


class _AssigneeProtocol(Protocol):
    """Protocol for PyGithub Assignee objects."""

    login: str


class _BranchRefProtocol(Protocol):
    """Protocol for PyGithub Branch ref objects."""

    ref: str


class _DatetimeLike(Protocol):
    """Protocol for datetime-like objects with isoformat method."""

    def isoformat(self) -> str: ...


class _IssueProtocol(Protocol):
    """Protocol for PyGithub Issue objects."""

    number: int
    title: str
    state: str
    html_url: str
    body: str | None
    created_at: _DatetimeLike
    updated_at: _DatetimeLike
    labels: list[_LabelProtocol]
    assignees: list[_AssigneeProtocol]


class _PullRequestProtocol(Protocol):
    """Protocol for PyGithub PullRequest objects."""

    number: int
    title: str
    state: str
    html_url: str
    body: str | None
    head: _BranchRefProtocol
    base: _BranchRefProtocol
    created_at: _DatetimeLike
    updated_at: _DatetimeLike
    draft: bool


def issue_to_info(issue: _IssueProtocol) -> IssueInfo:
    """Convert a PyGithub Issue object to IssueInfo."""
    return IssueInfo(
        number=issue.number,
        title=issue.title,
        state=issue.state,
        url=issue.html_url,
        body=issue.body,
        created_at=issue.created_at.isoformat(),
        updated_at=issue.updated_at.isoformat(),
        labels=[lb.name for lb in issue.labels],
        assignees=[a.login for a in issue.assignees],
    )


def pr_to_info(pr: _PullRequestProtocol) -> PullRequestInfo:
    """Convert a PyGithub PullRequest object to PullRequestInfo."""
    return PullRequestInfo(
        number=pr.number,
        title=pr.title,
        state=pr.state,
        url=pr.html_url,
        body=pr.body,
        head_ref=pr.head.ref,
        base_ref=pr.base.ref,
        created_at=pr.created_at.isoformat(),
        updated_at=pr.updated_at.isoformat(),
        draft=pr.draft,
    )
