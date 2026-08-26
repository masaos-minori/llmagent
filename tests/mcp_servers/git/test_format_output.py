"""tests/mcp_servers/git/test_format_output.py

Characterization tests for scripts/mcp_servers/git/format_output.py.

These tests lock the exact visible-output strings produced by each
``format_*`` function against mocked ``git.Repo`` objects, so a later
refactor of this module can be verified not to change behavior.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from mcp_servers.git.format_output import (
    GIT_SHOW_OUTPUT_MAX_CHARS,
    format_add,
    format_branch,
    format_checkout,
    format_commit,
    format_diff,
    format_log,
    format_pull,
    format_push,
    format_show,
    format_status,
)
from mcp_servers.git.git_models import (
    GitAddRequest,
    GitCheckoutRequest,
    GitCommitRequest,
    GitDiffRequest,
    GitLogRequest,
    GitPullRequest,
    GitPushRequest,
    GitServiceError,
    GitShowRequest,
)

REPO_PATH = "/tmp/repo"


# ── format_status ──────────────────────────────────────────────────────────


class TestFormatStatus:
    def test_clean_working_tree(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "main"
        repo.is_dirty.return_value = False
        result = format_status(repo)
        assert result == "On branch main\nNothing to commit, working tree clean"

    def test_dirty_with_modified_staged_and_untracked(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "feature/x"
        repo.is_dirty.return_value = True
        modified_item = MagicMock()
        modified_item.a_path = "modified.py"
        staged_item = MagicMock()
        staged_item.a_path = "staged.py"
        repo.untracked_files = ["new.py"]

        def diff_side_effect(target):
            if target is None:
                return [modified_item]
            return [staged_item]

        repo.index.diff.side_effect = diff_side_effect
        result = format_status(repo)
        assert result == (
            "On branch feature/x\n"
            "Changes present:\n"
            "  modified: modified.py\n"
            "  staged:   staged.py\n"
            "  untracked: new.py"
        )
        repo.is_dirty.assert_called_once_with(untracked_files=True)


# ── format_log ──────────────────────────────────────────────────────────────


class TestFormatLog:
    def _commit(
        self, sha: str, author: str, date_str: str, message: object
    ) -> MagicMock:
        commit = MagicMock()
        commit.hexsha = sha
        commit.author.name = author
        commit.committed_datetime.strftime.return_value = date_str
        commit.message = message
        return commit

    def test_no_commits_returns_placeholder(self) -> None:
        repo = MagicMock()
        repo.head.commit = "HEAD_SHA"
        repo.iter_commits.return_value = []
        req = GitLogRequest(repo_path=REPO_PATH, max_entries=20, branch="")
        result = format_log(repo, req, max_log_entries=50)
        assert result == "(no commits)"

    def test_str_message_formatted_and_truncated(self) -> None:
        repo = MagicMock()
        repo.head.commit = "HEAD_SHA"
        long_first_line = "x" * 100
        commit = self._commit(
            "abcdef1234567890", "Alice", "2026-01-02", f"{long_first_line}\nbody line"
        )
        repo.iter_commits.return_value = [commit]
        req = GitLogRequest(repo_path=REPO_PATH, max_entries=20, branch="")
        result = format_log(repo, req, max_log_entries=50)
        expected_short = long_first_line[:80]
        assert result == f"abcdef12 Alice 2026-01-02 {expected_short}"

    def test_bytes_message_decoded(self) -> None:
        repo = MagicMock()
        repo.head.commit = "HEAD_SHA"
        commit = self._commit("1111222233334444", "Bob", "2026-03-04", b"byte message")
        repo.iter_commits.return_value = [commit]
        req = GitLogRequest(repo_path=REPO_PATH, max_entries=20, branch="")
        result = format_log(repo, req, max_log_entries=50)
        assert result == "11112222 Bob 2026-03-04 byte message"

    def test_branch_selects_rev_and_limit_is_min_of_request_and_max(self) -> None:
        repo = MagicMock()
        repo.iter_commits.return_value = []
        req = GitLogRequest(repo_path=REPO_PATH, max_entries=100, branch="develop")
        format_log(repo, req, max_log_entries=5)
        repo.iter_commits.assert_called_once_with(rev="develop", max_count=5)

    def test_multiple_commits_joined_by_newline(self) -> None:
        repo = MagicMock()
        repo.head.commit = "HEAD_SHA"
        c1 = self._commit("aaaa1111aaaa1111", "A", "2026-01-01", "first")
        c2 = self._commit("bbbb2222bbbb2222", "B", "2026-01-02", "second")
        repo.iter_commits.return_value = [c1, c2]
        req = GitLogRequest(repo_path=REPO_PATH, max_entries=20, branch="")
        result = format_log(repo, req, max_log_entries=50)
        assert result == ("aaaa1111 A 2026-01-01 first\nbbbb2222 B 2026-01-02 second")


# ── format_diff ───────────────────────────────────────────────────────────────


class TestFormatDiff:
    def test_no_diff_returns_placeholder(self) -> None:
        repo = MagicMock()
        repo.git.diff.return_value = ""
        req = GitDiffRequest(repo_path=REPO_PATH, staged=False, commit="")
        result = format_diff(repo, req)
        assert result == "(no diff)"
        repo.git.diff.assert_called_once_with()

    def test_commit_ref_takes_priority(self) -> None:
        repo = MagicMock()
        repo.git.diff.return_value = "some diff text"
        req = GitDiffRequest(repo_path=REPO_PATH, staged=True, commit="HEAD~1")
        result = format_diff(repo, req)
        assert result == "some diff text"
        repo.git.diff.assert_called_once_with("HEAD~1")

    def test_staged_uses_cached_flag(self) -> None:
        repo = MagicMock()
        repo.git.diff.return_value = "staged diff"
        req = GitDiffRequest(repo_path=REPO_PATH, staged=True, commit="")
        result = format_diff(repo, req)
        assert result == "staged diff"
        repo.git.diff.assert_called_once_with("--cached")


# ── format_branch ─────────────────────────────────────────────────────────────


class TestFormatBranch:
    def test_no_branches_returns_placeholder(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "main"
        repo.branches = []
        result = format_branch(repo)
        assert result == "(no branches)"

    def test_current_branch_marked_with_asterisk(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "main"
        b1 = MagicMock()
        b1.name = "main"
        b2 = MagicMock()
        b2.name = "feature/x"
        repo.branches = [b1, b2]
        result = format_branch(repo)
        assert result == "* main\n  feature/x"


# ── format_show ────────────────────────────────────────────────────────────────


class TestFormatShow:
    def test_short_output_returned_as_is(self) -> None:
        repo = MagicMock()
        repo.git.show.return_value = "short output"
        req = GitShowRequest(repo_path=REPO_PATH, ref="HEAD")
        result = format_show(repo, req)
        assert result == "short output"
        repo.git.show.assert_called_once_with("HEAD", "--stat", "--patch")

    def test_long_output_truncated_at_max_chars(self) -> None:
        repo = MagicMock()
        long_output = "a" * (GIT_SHOW_OUTPUT_MAX_CHARS + 500)
        repo.git.show.return_value = long_output
        req = GitShowRequest(repo_path=REPO_PATH, ref="abc123")
        result = format_show(repo, req)
        assert result == long_output[:GIT_SHOW_OUTPUT_MAX_CHARS]
        assert len(result) == GIT_SHOW_OUTPUT_MAX_CHARS


# ── format_add ─────────────────────────────────────────────────────────────────


class TestFormatAdd:
    def test_dry_run_shows_untracked_and_modified(self) -> None:
        repo = MagicMock()
        repo.untracked_files = ["new.py", "other.txt"]
        modified_item = MagicMock()
        modified_item.a_path = "mod.py"
        repo.index.diff.return_value = [modified_item]
        req = GitAddRequest(
            repo_path=REPO_PATH, paths=["new.py", "mod.py"], dry_run=True
        )
        result = format_add(repo, req)
        assert result == "[DRY RUN] Would stage: ['mod.py', 'new.py']"

    def test_real_stage_calls_index_add_and_reports_paths(self) -> None:
        repo = MagicMock()
        req = GitAddRequest(repo_path=REPO_PATH, paths=["a.py", "b.py"], dry_run=False)
        result = format_add(repo, req)
        repo.index.add.assert_called_once_with(["a.py", "b.py"])
        assert result == "Staged: ['a.py', 'b.py']"


# ── format_commit ──────────────────────────────────────────────────────────────


class TestFormatCommit:
    def test_dry_run_reports_staged_files_and_message(self) -> None:
        repo = MagicMock()
        staged_item = MagicMock()
        staged_item.a_path = "file.py"
        repo.index.diff.return_value = [staged_item]
        req = GitCommitRequest(repo_path=REPO_PATH, message="feat: x", dry_run=True)
        result = format_commit(repo, req)
        assert (
            result
            == "[DRY RUN] Would commit 1 file(s): ['file.py']\nMessage: 'feat: x'"
        )

    def test_raises_when_nothing_staged(self) -> None:
        repo = MagicMock()
        repo.index.diff.return_value = []
        req = GitCommitRequest(repo_path=REPO_PATH, message="msg", dry_run=False)
        with pytest.raises(GitServiceError, match="nothing staged to commit"):
            format_commit(repo, req)

    def test_commits_and_reports_hexsha_and_message(self) -> None:
        repo = MagicMock()
        staged_item = MagicMock()
        staged_item.a_path = "file.py"
        repo.index.diff.return_value = [staged_item]
        commit_result = MagicMock()
        commit_result.hexsha = "0123456789abcdef"
        repo.index.commit.return_value = commit_result
        req = GitCommitRequest(repo_path=REPO_PATH, message="feat: y", dry_run=False)
        result = format_commit(repo, req)
        repo.index.commit.assert_called_once_with("feat: y")
        assert result == "Committed: 01234567 'feat: y'"


# ── format_checkout ────────────────────────────────────────────────────────────


class TestFormatCheckout:
    def test_dry_run_checkout_existing_branch(self) -> None:
        repo = MagicMock()
        req = GitCheckoutRequest(
            repo_path=REPO_PATH, branch="feature/x", create=False, dry_run=True
        )
        result = format_checkout(repo, req)
        assert result == "[DRY RUN] Would checkout 'feature/x'"

    def test_dry_run_create_branch(self) -> None:
        repo = MagicMock()
        req = GitCheckoutRequest(
            repo_path=REPO_PATH, branch="new-feat", create=True, dry_run=True
        )
        result = format_checkout(repo, req)
        assert result == "[DRY RUN] Would create and checkout 'new-feat'"

    def test_create_branch_checks_out_new_head(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "new-feat"
        repo.head.is_detached = False
        new_branch = MagicMock()
        repo.create_head.return_value = new_branch
        req = GitCheckoutRequest(
            repo_path=REPO_PATH, branch="new-feat", create=True, dry_run=False
        )
        result = format_checkout(repo, req)
        repo.create_head.assert_called_once_with("new-feat")
        new_branch.checkout.assert_called_once_with()
        assert result == "Switched to branch 'new-feat'"

    def test_existing_branch_uses_git_checkout(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "main"
        repo.head.is_detached = False
        req = GitCheckoutRequest(
            repo_path=REPO_PATH, branch="main", create=False, dry_run=False
        )
        result = format_checkout(repo, req)
        repo.git.checkout.assert_called_once_with("--", "main")
        assert result == "Switched to branch 'main'"

    def test_detached_head_denied_by_default(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "<detached HEAD>"
        repo.head.is_detached = True
        req = GitCheckoutRequest(
            repo_path=REPO_PATH, branch="develop", create=False, dry_run=False
        )
        with pytest.raises(GitServiceError, match="checkout postcondition failed"):
            format_checkout(repo, req)

    def test_detached_head_allowed_when_flag_set(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "develop"
        repo.head.is_detached = True
        req = GitCheckoutRequest(
            repo_path=REPO_PATH, branch="develop", create=False, dry_run=False
        )
        result = format_checkout(repo, req, allow_detached_head=True)
        assert result == "Switched to branch 'develop'"


# ── format_pull ────────────────────────────────────────────────────────────────


class TestFormatPull:
    def test_dry_run_with_no_fetch_output(self) -> None:
        repo = MagicMock()
        repo.git.fetch.return_value = ""
        req = GitPullRequest(
            repo_path=REPO_PATH, remote="origin", branch="", dry_run=True
        )
        result = format_pull(repo, req)
        assert result == "[DRY RUN] fetch --dry-run result:\n(nothing to commit)"
        repo.git.fetch.assert_called_once_with("--dry-run", "origin")

    def test_dry_run_with_fetch_output(self) -> None:
        repo = MagicMock()
        repo.git.fetch.return_value = "some fetch info"
        req = GitPullRequest(
            repo_path=REPO_PATH, remote="upstream", branch="", dry_run=True
        )
        result = format_pull(repo, req)
        assert result == "[DRY RUN] fetch --dry-run result:\nsome fetch info"

    def test_real_pull_without_branch(self) -> None:
        repo = MagicMock()
        repo.index.unmerged_blobs.return_value = []
        repo.git.pull.return_value = "pull output"
        req = GitPullRequest(
            repo_path=REPO_PATH, remote="origin", branch="", dry_run=False
        )
        result = format_pull(repo, req)
        repo.git.pull.assert_called_once_with("origin")
        assert result == "pull output"

    def test_real_pull_with_branch(self) -> None:
        repo = MagicMock()
        repo.index.unmerged_blobs.return_value = []
        repo.git.pull.return_value = "pull output"
        req = GitPullRequest(
            repo_path=REPO_PATH, remote="origin", branch="develop", dry_run=False
        )
        format_pull(repo, req)
        repo.git.pull.assert_called_once_with("origin", "--", "develop")

    def test_empty_pull_result_reports_up_to_date(self) -> None:
        repo = MagicMock()
        repo.index.unmerged_blobs.return_value = []
        repo.git.pull.return_value = ""
        req = GitPullRequest(
            repo_path=REPO_PATH, remote="origin", branch="", dry_run=False
        )
        result = format_pull(repo, req)
        assert result == "Already up to date."


class TestFormatPostconditionFailures:
    def test_checkout_postcondition_failure_wrong_branch(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "other-branch"
        repo.head.is_detached = False
        req = GitCheckoutRequest(
            repo_path=REPO_PATH, branch="main", create=False, dry_run=False
        )
        with pytest.raises(
            GitServiceError,
            match=r"checkout postcondition failed.*expected branch 'main'.*got 'other-branch'",
        ):
            format_checkout(repo, req)

    def test_checkout_postcondition_failure_detached_head(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "main"
        repo.head.is_detached = True
        req = GitCheckoutRequest(
            repo_path=REPO_PATH, branch="main", create=False, dry_run=False
        )
        with pytest.raises(
            GitServiceError,
            match=r"checkout postcondition failed.*expected branch 'main'.*detached HEAD",
        ):
            format_checkout(repo, req)

    def test_pull_postcondition_failure_unresolved_conflicts(self) -> None:
        repo = MagicMock()
        repo.index.unmerged_blobs.return_value = ["conflicted_file.py"]
        repo.git.pull.return_value = "pull output"
        req = GitPullRequest(
            repo_path=REPO_PATH, remote="origin", branch="", dry_run=False
        )
        with pytest.raises(
            GitServiceError,
            match=r"pull postcondition failed: unresolved merge conflicts remain",
        ):
            format_pull(repo, req)

    def test_push_postcondition_failure_rejection_marker_in_output(self) -> None:
        repo = MagicMock()
        repo.git.push.return_value = "! [rejected] main -> main (non-fast-forward)"
        req = GitPushRequest(
            repo_path=REPO_PATH, remote="origin", branch="main", dry_run=False
        )
        with pytest.raises(
            GitServiceError,
            match=r"push postcondition failed: rejection marker detected in output",
        ):
            format_push(repo, req)


# ── format_push ────────────────────────────────────────────────────────────────


class TestFormatPush:
    def test_dry_run_uses_explicit_branch(self) -> None:
        repo = MagicMock()
        req = GitPushRequest(
            repo_path=REPO_PATH, remote="origin", branch="feature/x", dry_run=True
        )
        result = format_push(repo, req)
        assert result == "[DRY RUN] Would push branch 'feature/x' to 'origin'"

    def test_dry_run_defaults_to_active_branch(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "main"
        req = GitPushRequest(
            repo_path=REPO_PATH, remote="origin", branch="", dry_run=True
        )
        result = format_push(repo, req)
        assert result == "[DRY RUN] Would push branch 'main' to 'origin'"

    def test_real_push_with_result(self) -> None:
        repo = MagicMock()
        repo.git.push.return_value = "push output"
        req = GitPushRequest(
            repo_path=REPO_PATH, remote="origin", branch="main", dry_run=False
        )
        result = format_push(repo, req)
        repo.git.push.assert_called_once_with("origin", "--", "main")
        assert result == "push output"

    def test_empty_push_result_reports_default_message(self) -> None:
        repo = MagicMock()
        repo.active_branch.name = "main"
        repo.git.push.return_value = ""
        req = GitPushRequest(
            repo_path=REPO_PATH, remote="origin", branch="", dry_run=False
        )
        result = format_push(repo, req)
        assert result == "Pushed 'main' to 'origin'"
