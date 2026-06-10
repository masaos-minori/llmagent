"""mcp/github/mapper.py
Mapper functions: convert PyGithub objects to Pydantic response models.

Extracted from service.py to separate conversion responsibility from business logic.
"""

from typing import Any

from mcp.github.models import IssueInfo, PullRequestInfo


def issue_to_info(issue: Any) -> IssueInfo:
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


def pr_to_info(pr: Any) -> PullRequestInfo:
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
