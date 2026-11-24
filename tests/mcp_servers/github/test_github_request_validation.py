"""
tests/mcp_servers/github/test_github_request_validation.py

T-03 model-level regression coverage for the strict GitHub request contract
(mcpai003 REQ-004 non-empty text and numbers >= 1, REQ-005 upper bounds,
REQ-008 one contract shared by discovery and runtime).

Every case calls `Model.model_validate(dict)` directly: the contract under test
is the model, not the dispatch path. `pydantic.ValidationError` is the raised
type here; the `GitHubValidationError` conversion and the HTTP boundary are
covered by `test_github_server_endpoints.py`.
"""

from __future__ import annotations

from typing import Any

import pytest
from mcp_servers.github.github_models_file import (
    CreateOrUpdateFileRequest,
    DeleteRepoFileRequest,
    GetFileContentsRequest,
    PushFilesRequest,
)
from mcp_servers.github.github_models_issues import (
    AddIssueCommentRequest,
    CreateIssueRequest,
    GetIssueRequest,
    ListIssuesRequest,
    SearchIssuesRequest,
)
from mcp_servers.github.github_models_pull_requests import (
    CreatePullRequestRequest,
    GetPullRequestRequest,
    ListPullRequestsRequest,
    MergePullRequestRequest,
    SearchPullRequestsRequest,
    UpdatePullRequestRequest,
)
from mcp_servers.github.github_models_repository import (
    CreateBranchRequest,
    GetCommitRequest,
    ListBranchesRequest,
    ListCommitsRequest,
    SearchCodeRequest,
    SearchRepositoriesRequest,
)
from pydantic import BaseModel, ValidationError

# The owner-confirmed upper bounds (Plan UNK-02) are the pinned contract: each is
# tested at the edge, one character or one item on both sides.
_TITLE_MAX = 256
_BODY_MAX = 65536
_CONTENT_MAX = 1048576
_LIST_MAX = 100
_PER_PAGE_MAX = 100


def _text(length: int) -> str:
    """Build one long string once instead of repeating literals in the tables."""
    return "x" * length


def _reject(model: type[BaseModel], payload: dict[str, Any], field: str) -> None:
    """Assert the model rejects `payload` because of `field`, not by accident.

    A field rule reports the field in `loc`; a `model_validator(mode="after")`
    sentinel rule reports at the model root (`loc` empty) and names the field in
    its message, so both shapes count.
    """
    with pytest.raises(ValidationError) as exc_info:
        model.model_validate(payload)
    errors = exc_info.value.errors()
    assert any(field in error["loc"] or field in error["msg"] for error in errors), (
        f"{model.__name__} rejected {payload} for the wrong reason: {errors}"
    )


def _accept(model: type[BaseModel], payload: dict[str, Any]) -> Any:
    """Assert the model accepts `payload` and return the validated instance."""
    return model.model_validate(payload)


class TestIssuesModel:
    """REQ-004/REQ-005 for the five issues request models (seq 03)."""

    @pytest.mark.parametrize(
        ("model", "payload", "field"),
        [
            (ListIssuesRequest, {"owner": "", "repo": "repo"}, "owner"),
            (ListIssuesRequest, {"owner": "owner", "repo": ""}, "repo"),
            (
                ListIssuesRequest,
                {"owner": "owner", "repo": "repo", "bogus": 1},
                "bogus",
            ),
            (
                ListIssuesRequest,
                {"owner": "owner", "repo": "repo", "per_page": 0},
                "per_page",
            ),
            (
                ListIssuesRequest,
                {"owner": "owner", "repo": "repo", "per_page": _PER_PAGE_MAX + 1},
                "per_page",
            ),
            (
                GetIssueRequest,
                {"owner": "owner", "repo": "repo", "issue_number": 0},
                "issue_number",
            ),
            (SearchIssuesRequest, {"query": ""}, "query"),
            (
                SearchIssuesRequest,
                {"query": "repo:owner/repo", "per_page": 0},
                "per_page",
            ),
            (
                CreateIssueRequest,
                {"owner": "owner", "repo": "repo", "title": ""},
                "title",
            ),
            (
                CreateIssueRequest,
                {"owner": "owner", "repo": "repo", "title": _text(_TITLE_MAX + 1)},
                "title",
            ),
            (
                CreateIssueRequest,
                {
                    "owner": "owner",
                    "repo": "repo",
                    "title": "t",
                    "body": _text(_BODY_MAX + 1),
                },
                "body",
            ),
            (
                CreateIssueRequest,
                {
                    "owner": "owner",
                    "repo": "repo",
                    "title": "t",
                    "labels": ["l"] * (_LIST_MAX + 1),
                },
                "labels",
            ),
            (
                CreateIssueRequest,
                {
                    "owner": "owner",
                    "repo": "repo",
                    "title": "t",
                    "assignees": ["a"] * (_LIST_MAX + 1),
                },
                "assignees",
            ),
            (
                AddIssueCommentRequest,
                {"owner": "owner", "repo": "repo", "issue_number": 0, "body": "b"},
                "issue_number",
            ),
            (
                AddIssueCommentRequest,
                {"owner": "owner", "repo": "repo", "issue_number": 1, "body": ""},
                "body",
            ),
            (
                AddIssueCommentRequest,
                {
                    "owner": "owner",
                    "repo": "repo",
                    "issue_number": 1,
                    "body": _text(_BODY_MAX + 1),
                },
                "body",
            ),
        ],
    )
    def test_invalid_arguments_are_rejected(
        self, model: type[BaseModel], payload: dict[str, Any], field: str
    ) -> None:
        _reject(model, payload, field)

    @pytest.mark.parametrize(
        ("model", "payload"),
        [
            (ListIssuesRequest, {"owner": "owner", "repo": "repo"}),
            (ListIssuesRequest, {"owner": "owner", "repo": "repo", "per_page": 1}),
            (
                ListIssuesRequest,
                {
                    "owner": "owner",
                    "repo": "repo",
                    "state": "all",
                    "per_page": _PER_PAGE_MAX,
                },
            ),
            (GetIssueRequest, {"owner": "owner", "repo": "repo", "issue_number": 1}),
            (SearchIssuesRequest, {"query": "repo:owner/repo is:issue", "per_page": 1}),
            (SearchIssuesRequest, {"query": "q", "per_page": _PER_PAGE_MAX}),
            (
                CreateIssueRequest,
                {
                    "owner": "owner",
                    "repo": "repo",
                    "title": _text(_TITLE_MAX),
                    "body": _text(_BODY_MAX),
                    "labels": ["l"] * _LIST_MAX,
                    "assignees": ["a"] * _LIST_MAX,
                    "dry_run": True,
                },
            ),
            (
                AddIssueCommentRequest,
                {
                    "owner": "owner",
                    "repo": "repo",
                    "issue_number": 1,
                    "body": _text(_BODY_MAX),
                },
            ),
        ],
    )
    def test_boundary_arguments_are_accepted(
        self, model: type[BaseModel], payload: dict[str, Any]
    ) -> None:
        _accept(model, payload)

    def test_state_pattern_accepts_the_three_documented_values(self) -> None:
        """`state` is a pattern, not a free string: open/closed/all pass, others fail."""
        for state in ("open", "closed", "all"):
            _accept(
                ListIssuesRequest, {"owner": "owner", "repo": "repo", "state": state}
            )
        _reject(
            ListIssuesRequest,
            {"owner": "owner", "repo": "repo", "state": "merged"},
            "state",
        )

    def test_default_per_page_is_ten(self) -> None:
        """The issues domain keeps its 10-item default (the repository domain uses 30)."""
        assert (
            ListIssuesRequest.model_validate({"owner": "o", "repo": "r"}).per_page == 10
        )
        assert SearchIssuesRequest.model_validate({"query": "q"}).per_page == 10


class TestPullRequestsModel:
    """REQ-004/REQ-005 for the six pull request request models (seq 04)."""

    @pytest.mark.parametrize(
        ("model", "payload", "field"),
        [
            (ListPullRequestsRequest, {"owner": "", "repo": "repo"}, "owner"),
            (ListPullRequestsRequest, {"owner": "owner", "repo": ""}, "repo"),
            (ListPullRequestsRequest, {"owner": "o", "repo": "r", "bogus": 1}, "bogus"),
            (
                ListPullRequestsRequest,
                {"owner": "o", "repo": "r", "per_page": 0},
                "per_page",
            ),
            (
                ListPullRequestsRequest,
                {"owner": "o", "repo": "r", "per_page": _PER_PAGE_MAX + 1},
                "per_page",
            ),
            (
                GetPullRequestRequest,
                {"owner": "o", "repo": "r", "pr_number": 0},
                "pr_number",
            ),
            (
                CreatePullRequestRequest,
                {"owner": "o", "repo": "r", "title": "t", "head": "", "base": "main"},
                "head",
            ),
            (
                CreatePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "title": "t",
                    "head": "feature",
                    "base": "",
                },
                "base",
            ),
            (
                CreatePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "title": _text(_TITLE_MAX + 1),
                    "head": "h",
                    "base": "b",
                },
                "title",
            ),
            (
                CreatePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "title": "t",
                    "head": "h",
                    "base": "b",
                    "body": _text(_BODY_MAX + 1),
                },
                "body",
            ),
            (
                CreatePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "title": "t",
                    "head": "h",
                    "base": "b",
                    "bogus": 1,
                },
                "bogus",
            ),
            (SearchPullRequestsRequest, {"query": ""}, "query"),
            (
                SearchPullRequestsRequest,
                {"query": "is:pr", "per_page": 101},
                "per_page",
            ),
            (
                UpdatePullRequestRequest,
                {"owner": "o", "repo": "r", "pr_number": 0},
                "pr_number",
            ),
            (
                UpdatePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "pr_number": 1,
                    "title": _text(_TITLE_MAX + 1),
                },
                "title",
            ),
            (
                UpdatePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "pr_number": 1,
                    "body": _text(_BODY_MAX + 1),
                },
                "body",
            ),
            (
                UpdatePullRequestRequest,
                {"owner": "o", "repo": "r", "pr_number": 1, "state": "merged"},
                "state",
            ),
            (
                MergePullRequestRequest,
                {"owner": "o", "repo": "r", "pr_number": 0},
                "pr_number",
            ),
            (
                MergePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "pr_number": 1,
                    "commit_title": _text(_TITLE_MAX + 1),
                },
                "commit_title",
            ),
            (
                MergePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "pr_number": 1,
                    "commit_message": _text(_BODY_MAX + 1),
                },
                "commit_message",
            ),
            (
                MergePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "pr_number": 1,
                    "merge_method": "fast-forward",
                },
                "merge_method",
            ),
        ],
    )
    def test_invalid_arguments_are_rejected(
        self, model: type[BaseModel], payload: dict[str, Any], field: str
    ) -> None:
        _reject(model, payload, field)

    @pytest.mark.parametrize(
        ("model", "payload"),
        [
            (ListPullRequestsRequest, {"owner": "o", "repo": "r"}),
            (
                ListPullRequestsRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "state": "closed",
                    "per_page": _PER_PAGE_MAX,
                },
            ),
            (GetPullRequestRequest, {"owner": "o", "repo": "r", "pr_number": 1}),
            (
                CreatePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "title": _text(_TITLE_MAX),
                    "body": _text(_BODY_MAX),
                    "head": "feature",
                    "base": "main",
                },
            ),
            (SearchPullRequestsRequest, {"query": "is:pr", "per_page": 1}),
            (SearchPullRequestsRequest, {"query": "is:pr", "per_page": _PER_PAGE_MAX}),
            (
                UpdatePullRequestRequest,
                {"owner": "o", "repo": "r", "pr_number": 1, "state": "open"},
            ),
            (
                UpdatePullRequestRequest,
                {"owner": "o", "repo": "r", "pr_number": 1, "body": ""},
            ),
            (
                UpdatePullRequestRequest,
                {"owner": "o", "repo": "r", "pr_number": 1, "title": _text(_TITLE_MAX)},
            ),
            (
                MergePullRequestRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "pr_number": 1,
                    "commit_title": _text(_TITLE_MAX),
                    "commit_message": _text(_BODY_MAX),
                    "merge_method": "squash",
                },
            ),
        ],
    )
    def test_boundary_arguments_are_accepted(
        self, model: type[BaseModel], payload: dict[str, Any]
    ) -> None:
        _accept(model, payload)

    def test_update_pull_request_requires_a_field(self) -> None:
        """A no-op update is rejected; one supplied field is enough (REQ-004)."""
        with pytest.raises(ValidationError) as exc_info:
            UpdatePullRequestRequest.model_validate(
                {"owner": "o", "repo": "r", "pr_number": 1}
            )
        message = str(exc_info.value)
        for name in ("title", "body", "state"):
            assert name in message, f"no-op error does not name {name}: {message}"

        # An explicit None means 'keep', so it is still a no-op. The after-validator
        # reports it at the model root, so the loc is empty.
        with pytest.raises(ValidationError, match="at least one of title, body, state"):
            UpdatePullRequestRequest.model_validate(
                {
                    "owner": "o",
                    "repo": "r",
                    "pr_number": 1,
                    "title": None,
                    "body": None,
                    "state": None,
                }
            )

        _accept(
            UpdatePullRequestRequest,
            {"owner": "o", "repo": "r", "pr_number": 1, "state": "open"},
        )

    def test_default_per_page_is_ten(self) -> None:
        """The pull request domain keeps its 10-item default."""
        assert (
            ListPullRequestsRequest.model_validate({"owner": "o", "repo": "r"}).per_page
            == 10
        )
        assert SearchPullRequestsRequest.model_validate({"query": "q"}).per_page == 10


class TestFileModel:
    """REQ-004/REQ-005 for the four file request models and nested `PushFile` (seq 05)."""

    @pytest.mark.parametrize(
        ("model", "payload", "field"),
        [
            (GetFileContentsRequest, {"owner": "", "repo": "r", "path": "p"}, "owner"),
            (GetFileContentsRequest, {"owner": "o", "repo": "", "path": "p"}, "repo"),
            (GetFileContentsRequest, {"owner": "o", "repo": "r", "path": ""}, "path"),
            (
                GetFileContentsRequest,
                {"owner": "o", "repo": "r", "path": "p", "bogus": 1},
                "bogus",
            ),
            (
                CreateOrUpdateFileRequest,
                {"owner": "o", "repo": "r", "path": "", "content": "c", "message": "m"},
                "path",
            ),
            (
                CreateOrUpdateFileRequest,
                {"owner": "o", "repo": "r", "path": "p", "content": "c", "message": ""},
                "message",
            ),
            (
                CreateOrUpdateFileRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "path": "p",
                    "content": "c",
                    "message": "m",
                    "bogus": 1,
                },
                "bogus",
            ),
            (
                CreateOrUpdateFileRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "path": "p",
                    "content": _text(_CONTENT_MAX + 1),
                    "message": "m",
                },
                "content",
            ),
            (
                PushFilesRequest,
                {"owner": "o", "repo": "r", "branch": "b", "message": "m", "files": []},
                "files",
            ),
            (
                PushFilesRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "branch": "b",
                    "message": "m",
                    "files": [{"path": "a", "content": "c", "bogus": 1}],
                },
                "bogus",
            ),
            (
                PushFilesRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "branch": "b",
                    "message": "m",
                    "files": [{"path": "", "content": "c"}],
                },
                "path",
            ),
            (
                PushFilesRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "branch": "b",
                    "message": "m",
                    "files": [{"path": "a", "content": _text(_CONTENT_MAX + 1)}],
                },
                "content",
            ),
            (
                PushFilesRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "branch": "b",
                    "message": "m",
                    "files": [
                        {"path": f"f{i}", "content": "c"} for i in range(_LIST_MAX + 1)
                    ],
                },
                "files",
            ),
            (
                PushFilesRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "branch": "",
                    "message": "m",
                    "files": [{"path": "a", "content": "c"}],
                },
                "branch",
            ),
            (
                DeleteRepoFileRequest,
                {"owner": "o", "repo": "r", "path": "p", "message": "m", "sha": ""},
                "sha",
            ),
            (
                DeleteRepoFileRequest,
                {"owner": "o", "repo": "r", "path": "p", "message": "", "sha": "abc"},
                "message",
            ),
        ],
    )
    def test_invalid_arguments_are_rejected(
        self, model: type[BaseModel], payload: dict[str, Any], field: str
    ) -> None:
        _reject(model, payload, field)

    @pytest.mark.parametrize(
        ("model", "payload"),
        [
            (GetFileContentsRequest, {"owner": "o", "repo": "r", "path": "p"}),
            (
                GetFileContentsRequest,
                {"owner": "o", "repo": "r", "path": "p", "ref": "main"},
            ),
            (
                CreateOrUpdateFileRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "path": "p",
                    "content": _text(_CONTENT_MAX),
                    "message": "m",
                },
            ),
            (
                CreateOrUpdateFileRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "path": "p",
                    "content": "c",
                    "message": "m",
                    "branch": "feature",
                    "sha": "abc123",
                    "dry_run": True,
                },
            ),
            (
                PushFilesRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "branch": "feature",
                    "message": "m",
                    "files": [{"path": "a", "content": _text(_CONTENT_MAX)}],
                },
            ),
            (
                PushFilesRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "branch": "feature",
                    "message": "m",
                    "files": [
                        {"path": f"f{i}", "content": "c"} for i in range(_LIST_MAX)
                    ],
                },
            ),
            (
                DeleteRepoFileRequest,
                {"owner": "o", "repo": "r", "path": "p", "message": "m", "sha": "abc"},
            ),
            (
                DeleteRepoFileRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "path": "p",
                    "message": "m",
                    "sha": "abc",
                    "branch": "feature",
                },
            ),
        ],
    )
    def test_boundary_arguments_are_accepted(
        self, model: type[BaseModel], payload: dict[str, Any]
    ) -> None:
        _accept(model, payload)

    @pytest.mark.parametrize(
        ("model", "sentinel"),
        [
            (GetFileContentsRequest, "ref"),
            (CreateOrUpdateFileRequest, "branch"),
            (CreateOrUpdateFileRequest, "sha"),
            (DeleteRepoFileRequest, "branch"),
        ],
    )
    def test_empty_sentinel_is_rejected_only_when_supplied(
        self, model: type[BaseModel], sentinel: str
    ) -> None:
        """`{"ref": ""}` rejects; omitting the key keeps the documented default (REQ-004)."""
        payload = _minimal_valid_payload(model)
        _reject(model, {**payload, sentinel: ""}, sentinel)
        _accept(model, payload)

    def test_nested_push_file_rejects_unknown_keys(self) -> None:
        """`files` items are strict too: a typo inside one entry is not dropped."""
        _reject(
            PushFilesRequest,
            {
                "owner": "o",
                "repo": "r",
                "branch": "feature",
                "message": "m",
                "files": [
                    {"path": "a", "content": "c"},
                    {"path": "b", "content": "d", "bogus": 1},
                ],
            },
            "bogus",
        )


class TestRepositoryModel:
    """REQ-004/REQ-005 for the six repository request models (seq 06)."""

    @pytest.mark.parametrize(
        ("model", "payload", "field"),
        [
            (SearchRepositoriesRequest, {"query": ""}, "query"),
            (SearchRepositoriesRequest, {"query": "q", "per_page": 0}, "per_page"),
            (
                SearchRepositoriesRequest,
                {"query": "q", "per_page": _PER_PAGE_MAX + 1},
                "per_page",
            ),
            (ListCommitsRequest, {"owner": "o", "repo": "", "per_page": 30}, "repo"),
            (
                ListCommitsRequest,
                {"owner": "o", "repo": "r", "per_page": 0},
                "per_page",
            ),
            (
                ListCommitsRequest,
                {"owner": "o", "repo": "r", "per_page": _PER_PAGE_MAX + 1},
                "per_page",
            ),
            (ListCommitsRequest, {"owner": "o", "repo": "r", "branch": ""}, "branch"),
            (SearchCodeRequest, {"query": ""}, "query"),
            (SearchCodeRequest, {"query": "q", "per_page": 0}, "per_page"),
            (
                SearchCodeRequest,
                {"query": "q", "per_page": _PER_PAGE_MAX + 1},
                "per_page",
            ),
            (
                ListBranchesRequest,
                {"owner": "o", "repo": "r", "per_page": 0},
                "per_page",
            ),
            (
                ListBranchesRequest,
                {"owner": "o", "repo": "r", "per_page": _PER_PAGE_MAX + 1},
                "per_page",
            ),
            (GetCommitRequest, {"owner": "o", "repo": "r", "sha": ""}, "sha"),
            (
                CreateBranchRequest,
                {"owner": "o", "repo": "r", "branch_name": ""},
                "branch_name",
            ),
            (
                CreateBranchRequest,
                {"owner": "o", "repo": "r", "branch_name": "new", "from_branch": ""},
                "from_branch",
            ),
        ],
    )
    def test_invalid_arguments_are_rejected(
        self, model: type[BaseModel], payload: dict[str, Any], field: str
    ) -> None:
        _reject(model, payload, field)

    @pytest.mark.parametrize(
        ("model", "payload"),
        [
            (SearchRepositoriesRequest, {"query": "topic:ml"}),
            (SearchRepositoriesRequest, {"query": "q", "per_page": 1}),
            (SearchRepositoriesRequest, {"query": "q", "per_page": _PER_PAGE_MAX}),
            (ListCommitsRequest, {"owner": "o", "repo": "r"}),
            (
                ListCommitsRequest,
                {"owner": "o", "repo": "r", "branch": "feature", "per_page": 1},
            ),
            (
                ListCommitsRequest,
                {"owner": "o", "repo": "r", "per_page": _PER_PAGE_MAX},
            ),
            (SearchCodeRequest, {"query": "filename:agent.py", "per_page": 1}),
            (SearchCodeRequest, {"query": "q", "per_page": _PER_PAGE_MAX}),
            (ListBranchesRequest, {"owner": "o", "repo": "r"}),
            (
                ListBranchesRequest,
                {"owner": "o", "repo": "r", "per_page": _PER_PAGE_MAX},
            ),
            (GetCommitRequest, {"owner": "o", "repo": "r", "sha": "abc123"}),
            (CreateBranchRequest, {"owner": "o", "repo": "r", "branch_name": "new"}),
            (
                CreateBranchRequest,
                {
                    "owner": "o",
                    "repo": "r",
                    "branch_name": "new",
                    "from_branch": "main",
                    "dry_run": True,
                },
            ),
        ],
    )
    def test_boundary_arguments_are_accepted(
        self, model: type[BaseModel], payload: dict[str, Any]
    ) -> None:
        _accept(model, payload)

    @pytest.mark.parametrize(
        ("model", "payload"),
        [
            (SearchRepositoriesRequest, {"query": "q"}),
            (ListCommitsRequest, {"owner": "o", "repo": "r"}),
            (SearchCodeRequest, {"query": "q"}),
            (ListBranchesRequest, {"owner": "o", "repo": "r"}),
        ],
    )
    def test_default_per_page_is_thirty(
        self, model: type[BaseModel], payload: dict[str, Any]
    ) -> None:
        """The four paginated repository tools publish a default of 30 (seq 06 decision)."""
        assert model.model_validate(payload).per_page == 30

    @pytest.mark.parametrize(
        ("model", "sentinel"),
        [
            (ListCommitsRequest, "branch"),
            (CreateBranchRequest, "from_branch"),
        ],
    )
    def test_empty_sentinel_is_rejected_only_when_supplied(
        self, model: type[BaseModel], sentinel: str
    ) -> None:
        """`{"branch": ""}` rejects; omitting the key keeps the default branch (REQ-004)."""
        payload = _minimal_valid_payload(model)
        _reject(model, {**payload, sentinel: ""}, sentinel)
        _accept(model, payload)


def _minimal_valid_payload(model: type[BaseModel]) -> dict[str, Any]:
    """One accepted payload per model, used by the sentinel tests."""
    payloads: dict[type[BaseModel], dict[str, Any]] = {
        GetFileContentsRequest: {"owner": "o", "repo": "r", "path": "p"},
        CreateOrUpdateFileRequest: {
            "owner": "o",
            "repo": "r",
            "path": "p",
            "content": "c",
            "message": "m",
        },
        DeleteRepoFileRequest: {
            "owner": "o",
            "repo": "r",
            "path": "p",
            "message": "m",
            "sha": "abc",
        },
        ListCommitsRequest: {"owner": "o", "repo": "r"},
        CreateBranchRequest: {"owner": "o", "repo": "r", "branch_name": "new"},
    }
    return dict(payloads[model])
