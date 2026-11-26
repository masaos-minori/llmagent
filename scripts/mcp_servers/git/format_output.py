#!/usr/bin/env python3
"""scripts/mcp_servers/git/format_output.py

Output formatting for git-mcp operations.

Dependency direction: mcp_servers.git.format_output → git (GitPython)
Import from here:  from mcp_servers.git.format_output import format_status, format_log, format_diff, format_branch, format_show, format_add, format_commit, format_checkout, format_pull, format_push
"""

from __future__ import annotations

import os
import signal
import subprocess  # nosec B404 — the write path runs the git CLI in its own process group

import git
import git.exc
from git.refs.remote import RemoteReference
from git.remote import Remote

from mcp_servers.git.errors import GitPolicyError, GitServiceError
from mcp_servers.git.git_models import (
    GitAddRequest,
    GitCheckoutRequest,
    GitCommitRequest,
    GitConfig,
    GitDiffRequest,
    GitLogRequest,
    GitPullRequest,
    GitPushRequest,
    GitShowRequest,
)
from mcp_servers.git.repository_state import (
    RepositoryState,
    _normalize_branch_name,
    _query_or_default,
    _redact_remote_url,
    _resolve_remote_url,
)

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
        raise GitPolicyError("nothing staged to commit")
    commit = repo.index.commit(req.message)
    return f"Committed: {commit.hexsha[:8]} {req.message!r}"


def _reject_wrong_branch(
    refreshed: RepositoryState, branch: str, allow_detached_head: bool
) -> None:
    """Raise when the refreshed state does not match the branch the checkout targeted."""
    if refreshed.active_branch != branch or (
        not allow_detached_head and refreshed.head_type == "detached"
    ):
        raise GitServiceError(
            f"checkout postcondition failed: state already changed; "
            f"expected branch {branch!r}, got "
            f"{'<detached HEAD>' if refreshed.head_type == 'detached' else refreshed.active_branch!r}"
        )


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
        state._repo.git.checkout(req.branch, "--")
    # Refresh state after checkout; git.Repo does not auto-update HEAD reference.
    # The refreshed snapshot is released through the context-manager form. If the
    # repo path is unavailable (e.g., mocked in tests), fall back to checking the
    # pre-snapshot state, which reflects the mock's behavior.
    try:
        with RepositoryState.snapshot(state.path) as refreshed:
            _reject_wrong_branch(refreshed, req.branch, allow_detached_head)
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
        _reject_wrong_branch(state, req.branch, allow_detached_head)
    return f"Switched to branch '{req.branch}'"


def _authorize_remote(state: RepositoryState, remote_name: str, cfg: GitConfig) -> None:
    """reject a remote whose current URL is not in
    ``cfg.allowed_remote_urls`` — must run before any mutating GitPython call.
    Raises GitServiceError with the redacted (never raw) resolved URL."""
    assert state._repo is not None
    url = _resolve_remote_url(state._repo, remote_name)
    redacted = _redact_remote_url(url) if url is not None else "(unknown remote)"
    if url is None or url not in cfg.allowed_remote_urls:
        raise GitPolicyError(
            f"[DENIED] remote {remote_name!r} ({redacted}) is not an authorized remote"
        )


def _run_git_write(
    state: RepositoryState,
    tool: str,
    argv: list[str],
    timeout: float | None,
) -> str:
    """Run one mutating `git` CLI call in its own process group and return stdout.

    The deadline is applied here, inside Stage 6's op, rather than at the async
    boundary: a synchronous GitPython call has no cancellation point, so stopping a
    network write at the deadline means terminating the process group. `Popen` +
    `communicate()` is used rather than `subprocess.run` because `run()` kills only
    the child on timeout, not the group.

    `subprocess.TimeoutExpired` propagates to the pipeline, which classifies the
    outcome as unknown; the formatter does not encode an outcome in its result text,
    because message text is not a contract.
    """
    # `git` is resolved from PATH and argv is a fixed list built from the validated
    # remote and branch names; shell=False, so no shell interpretation of the arguments
    # happens.
    proc = subprocess.Popen(  # nosec B603, B607 — fixed argv list, shell=False, no untrusted input
        ["git", *argv],
        cwd=state.path,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # The child is the group leader (start_new_session), so its pid is the group id.
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except OSError:
            pass
        proc.wait()
        raise
    if proc.returncode != 0:
        raise GitServiceError(f"{tool} failed: {(stderr or '').strip()}")
    return stdout


def _remote_ref_matches(post: RepositoryState, remote_name: str, branch: str) -> bool:
    """Return True when *remote_name*'s tracking ref for *branch* equals the post-state HEAD commit.

    A missing remote, a missing tracking ref, or an unreadable HEAD is a failure, not
    a pass. A snapshot with no repository handle (a test double, or a closed handle)
    cannot be checked and passes.
    """
    repo = post._repo
    if repo is None:
        return True
    remotes: list[Remote] = _query_or_default(lambda: list(repo.remotes), [])
    remote = next((r for r in remotes if r.name == remote_name), None)
    if remote is None:
        return False
    head = _query_or_default(lambda: repo.head.commit.hexsha, None)
    if head is None:
        return False
    target = _normalize_branch_name(branch)
    refs: list[RemoteReference] = _query_or_default(lambda: list(remote.refs), [])
    for ref in refs:
        name = ref.name
        tail = name.split("/", 1)[1] if "/" in name else name
        if _normalize_branch_name(tail) == target:
            return _query_or_default(lambda: ref.commit.hexsha, None) == head
    return False


def format_pull(
    state: RepositoryState,
    req: GitPullRequest,
    cfg: GitConfig,
    timeout: float | None = None,
) -> str:
    """Format output for fetching and merging remote changes.

    ``timeout`` (seconds) is the deadline applied inside this call: the write runs as
    a `git` CLI subprocess in its own process group, so a timeout terminates the
    process group instead of leaving a worker thread running past the deadline.
    ``None`` (the default) means no deadline.
    """
    _authorize_remote(state, req.remote, cfg)
    if req.dry_run:
        assert state._repo is not None
        fetch_info = state._repo.git.fetch("--dry-run", req.remote)
        return (
            f"[DRY RUN] fetch --dry-run result:\n{fetch_info or '(nothing to commit)'}"
        )
    pull_args = ["pull", req.remote]
    if req.branch:
        pull_args.extend(["--", req.branch])
    output = _run_git_write(state, "pull", pull_args, timeout)
    # Re-read the state for the postcondition: the subprocess changed the repository,
    # so the pre-operation snapshot cannot show what the write did.
    with RepositoryState.snapshot(state.path) as post:
        if post._repo is not None and post._repo.index.unmerged_blobs():
            raise GitServiceError(
                "pull postcondition failed: unresolved merge conflicts remain"
            )
    return output or "Already up to date."


def format_push(
    state: RepositoryState,
    req: GitPushRequest,
    cfg: GitConfig,
    timeout: float | None = None,
) -> str:
    """Format output for pushing local commits to a remote.

    ``timeout`` (seconds) is the deadline applied inside this call: the write runs as
    a `git` CLI subprocess in its own process group, so a timeout terminates the
    process group instead of leaving a worker thread running past the deadline.
    ``None`` (the default) means no deadline.
    """
    _authorize_remote(state, req.remote, cfg)
    branch = req.branch
    if req.dry_run:
        return f"[DRY RUN] Would push branch '{branch}' to '{req.remote}'"
    output = _run_git_write(state, "push", ["push", req.remote, "--", branch], timeout)
    # The remote name is in scope here but not at Stage 7, so the remote-ref part of
    # the postcondition is checked against the requested remote; Stage 7 makes the
    # same comparison from the snapshot side.
    with RepositoryState.snapshot(state.path) as post:
        if not _remote_ref_matches(post, req.remote, branch):
            raise GitServiceError(
                f"push postcondition failed: remote {req.remote!r} does not have "
                f"{branch!r} at the local HEAD commit"
            )
    return output or f"Pushed '{branch}' to '{req.remote}'"
