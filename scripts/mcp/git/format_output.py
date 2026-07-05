#!/usr/bin/env python3
"""mcp/git/format_output.py

Output formatting for git-mcp operations.

Dependency direction: mcp.git.format_output → git (GitPython)
Import from here:  from mcp.git.format_output import format_status, format_log, format_diff, format_branch, format_show, format_add, format_commit, format_checkout, format_pull, format_push
"""

from __future__ import annotations

import git

from mcp.git.models import (
    GitAddRequest,
    GitCheckoutRequest,
    GitCommitRequest,
    GitDiffRequest,
    GitLogRequest,
    GitPullRequest,
    GitPushRequest,
    GitShowRequest,
)

GIT_SHOW_OUTPUT_MAX_CHARS = 8000


def format_status(repo: git.Repo) -> str:
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


def format_log(repo: git.Repo, req: GitLogRequest, max_log_entries: int) -> str:
    limit = min(req.max_entries, max_log_entries)
    rev = req.branch or repo.head.commit
    commits = list(repo.iter_commits(rev=rev, max_count=limit))
    lines: list[str] = []
    for c in commits:
        raw_msg: str = (
            c.message.decode("utf-8", errors="replace")
            if isinstance(c.message, bytes)
            else c.message
        )
        short_msg = raw_msg.split("\n")[0][:80]
        lines.append(
            f"{c.hexsha[:8]} {c.author.name} {c.committed_datetime.strftime('%Y-%m-%d')} {short_msg}",
        )
    return "\n".join(lines) if lines else "(no commits)"


def format_diff(repo: git.Repo, req: GitDiffRequest) -> str:
    if req.commit:
        diff = repo.git.diff(req.commit)
    elif req.staged:
        diff = repo.git.diff("--cached")
    else:
        diff = repo.git.diff()
    return diff or "(no diff)"


def format_branch(repo: git.Repo) -> str:
    current = repo.active_branch.name
    branches = [
        f"* {b.name}" if b.name == current else f"  {b.name}" for b in repo.branches
    ]
    return "\n".join(branches) if branches else "(no branches)"


def format_show(repo: git.Repo, req: GitShowRequest) -> str:
    output: str = repo.git.show(req.ref, "--stat", "--patch")
    if len(output) > GIT_SHOW_OUTPUT_MAX_CHARS:
        return output[:GIT_SHOW_OUTPUT_MAX_CHARS]
    return output


def format_add(repo: git.Repo, req: GitAddRequest) -> str:
    if req.dry_run:
        untracked = {p for p in repo.untracked_files if p in req.paths}
        modified = {i.a_path for i in repo.index.diff(None) if i.a_path in req.paths}
        to_stage = untracked | modified
        return f"[DRY RUN] Would stage: {sorted(to_stage)}"
    repo.index.add(req.paths)
    return f"Staged: {req.paths}"


def format_commit(repo: git.Repo, req: GitCommitRequest) -> str:
    staged = [i.a_path for i in repo.index.diff("HEAD")]
    if req.dry_run:
        return f"[DRY RUN] Would commit {len(staged)} file(s): {staged}\nMessage: {req.message!r}"
    if not staged:
        from mcp.git.models import GitServiceError

        raise GitServiceError("nothing staged to commit")
    commit = repo.index.commit(req.message)
    return f"Committed: {commit.hexsha[:8]} {req.message!r}"


def format_checkout(repo: git.Repo, req: GitCheckoutRequest) -> str:
    if req.dry_run:
        action = (
            f"create and checkout '{req.branch}'"
            if req.create
            else f"checkout '{req.branch}'"
        )
        return f"[DRY RUN] Would {action}"
    if req.create:
        new_branch = repo.create_head(req.branch)
        new_branch.checkout()
    else:
        repo.git.checkout(req.branch)
    return f"Switched to branch '{req.branch}'"


def format_pull(repo: git.Repo, req: GitPullRequest) -> str:
    if req.dry_run:
        fetch_info = repo.git.fetch("--dry-run", req.remote)
        return (
            f"[DRY RUN] fetch --dry-run result:\n{fetch_info or '(nothing to fetch)'}"
        )
    pull_args = [req.remote]
    if req.branch:
        pull_args.append(req.branch)
    result = repo.git.pull(*pull_args)
    return result or "Already up to date."


def format_push(repo: git.Repo, req: GitPushRequest) -> str:
    branch = req.branch or repo.active_branch.name
    if req.dry_run:
        return f"[DRY RUN] Would push branch '{branch}' to '{req.remote}'"
    result = repo.git.push(req.remote, branch)
    return result or f"Pushed '{branch}' to '{req.remote}'"
