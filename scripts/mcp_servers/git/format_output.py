#!/usr/bin/env python3
"""scripts/mcp_servers/git/format_output.py

Output formatting for git-mcp operations.

Dependency direction: mcp_servers.git.format_output → git (GitPython)
Import from here:  from mcp_servers.git.format_output import format_status, format_log, format_diff, format_branch, format_show, format_add, format_commit, format_checkout, format_pull, format_push
"""

from __future__ import annotations

import git

from mcp_servers.git.errors import GitServiceError
from mcp_servers.git.git_models import (
    GitAddRequest,
    GitCheckoutRequest,
    GitCommitRequest,
    GitDiffRequest,
    GitLogRequest,
    GitPullRequest,
    GitPushRequest,
    GitShowRequest,
)
from mcp_servers.git.repository_state import RepositoryState

GIT_SHOW_OUTPUT_MAX_CHARS = 8000


def format_status(repo: git.Repo) -> str:
    """Format repository status including branches, dirty state, and untracked files."""
    lines: list[str] = []
    lines.append(f"On branch {repo.active_branch.name}")
    if repo.is_dirty(untracked_files=True):
        lines.append("Changes present:")
        for item in repo.index.diff(None):
            lines.append(f"  modified: {item.a_path}")
        for item in repo.index.diff("HEAD"):
            lines.append(f"  staged:   {item.a_path}")
        for path in repo.untracked_files:
            lines.append(f"  untracked: {path}")
    else:
        lines.append("Nothing to commit, working tree clean")
    return "\n".join(lines)


def _decode_commit_message(message: str | bytes) -> str:
    """Decode a commit message to str, tolerating non-UTF-8 byte sequences."""
    if isinstance(message, bytes):
        return message.decode("utf-8", errors="replace")
    return message


def format_log(repo: git.Repo, req: GitLogRequest, max_log_entries: int) -> str:
    """Format recent commit log entries."""
    limit = min(req.max_entries, max_log_entries)
    rev = req.branch or repo.head.commit
    commits = list(repo.iter_commits(rev=rev, max_count=limit))
    lines: list[str] = []
    for c in commits:
        raw_msg = _decode_commit_message(c.message)
        short_msg = raw_msg.split("\n")[0][:80]
        lines.append(
            f"{c.hexsha[:8]} {c.author.name} {c.committed_datetime.strftime('%Y-%m-%d')} {short_msg}",
        )
    return "\n".join(lines) if lines else "(no commits)"


def format_diff(repo: git.Repo, req: GitDiffRequest) -> str:
    """Format diff between working tree and index or two commits."""
    if req.commit:
        diff = repo.git.diff(req.commit)
    elif req.staged:
        diff = repo.git.diff("--cached")
    else:
        diff = repo.git.diff()
    return diff or "(no diff)"


def format_branch(repo: git.Repo) -> str:
    """Format list of branches with the current one marked."""
    current = repo.active_branch.name
    branches = [
        f"* {b.name}" if b.name == current else f"  {b.name}" for b in repo.branches
    ]
    return "\n".join(branches) if branches else "(no branches)"


def format_show(repo: git.Repo, req: GitShowRequest) -> str:
    """Format details of a commit, blob, or tree object."""
    output: str = repo.git.show(req.ref, "--stat", "--patch")
    if len(output) > GIT_SHOW_OUTPUT_MAX_CHARS:
        return output[:GIT_SHOW_OUTPUT_MAX_CHARS]
    return output


def format_add(repo: git.Repo, req: GitAddRequest) -> str:
    """Format output for staging files."""
    if req.dry_run:
        untracked = {p for p in repo.untracked_files if p in req.paths}
        modified = {i.a_path for i in repo.index.diff(None) if i.a_path in req.paths}
        to_stage = untracked | modified
        return f"[DRY RUN] Would stage: {sorted(p for p in to_stage if p is not None)}"
    repo.index.add(req.paths)
    return f"Staged: {req.paths}"


def format_commit(repo: git.Repo, req: GitCommitRequest) -> str:
    """Format output for creating a new commit."""
    staged = [i.a_path for i in repo.index.diff("HEAD")]
    if req.dry_run:
        return f"[DRY RUN] Would commit {len(staged)} file(s): {staged}\nMessage: {req.message!r}"
    if not staged:
        raise GitServiceError("nothing staged to commit")
    commit = repo.index.commit(req.message)
    return f"Committed: {commit.hexsha[:8]} {req.message!r}"


def format_checkout(
    state: RepositoryState,
    req: GitCheckoutRequest,
    *,
    allow_detached_head: bool = False,
) -> str:
    """Format output for switching branches."""
    if req.dry_run:
        action = (
            f"create and checkout '{req.branch}'"
            if req.create
            else f"checkout '{req.branch}'"
        )
        return f"[DRY RUN] Would {action}"
    if req.create:
        assert state._repo is not None
        new_branch = state._repo.create_head(req.branch)
        new_branch.checkout()
    else:
        # Use '--' to prevent argument injection if req.branch starts with '-'
        assert state._repo is not None
        state._repo.git.checkout("--", req.branch)
    if state.active_branch != req.branch or (
        not allow_detached_head and state.head_type == "detached"
    ):
        raise GitServiceError(
            f"checkout postcondition failed: expected branch {req.branch!r}, "
            f"got {'<detached HEAD>' if state.head_type == 'detached' else state.active_branch!r}"
        )
    return f"Switched to branch '{req.branch}'"


def format_pull(state: RepositoryState, req: GitPullRequest) -> str:
    """Format output for fetching and merging remote changes."""
    if req.dry_run:
        assert state._repo is not None
        fetch_info = state._repo.git.fetch("--dry-run", req.remote)
        return (
            f"[DRY RUN] fetch --dry-run result:\n{fetch_info or '(nothing to commit)'}"
        )
    pull_args = [req.remote]
    if req.branch:
        pull_args.extend(["--", req.branch])
    assert state._repo is not None
    result = state._repo.git.pull(*pull_args)
    assert state._repo is not None
    if state._repo.index.unmerged_blobs():
        raise GitServiceError(
            "pull postcondition failed: unresolved merge conflicts remain"
        )
    return result or "Already up to date."


def format_push(state: RepositoryState, req: GitPushRequest) -> str:
    """Format output for pushing local commits to a remote."""
    branch = req.branch or state.active_branch
    if req.dry_run:
        return f"[DRY RUN] Would push branch '{branch}' to '{req.remote}'"
    assert state._repo is not None
    result = state._repo.git.push(req.remote, "--", branch)
    _rejection_markers = ("[rejected]", "non-fast-forward", "failed to push")
    if result and any(m in result for m in _rejection_markers):
        raise GitServiceError(
            f"push postcondition failed: rejection marker detected in output: {result!r}"
        )
    return result or f"Pushed '{branch}' to '{req.remote}'"
