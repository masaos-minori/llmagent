#!/usr/bin/env python3
"""scripts/shared/repo_identity.py — Canonical repository identity helpers.

Defines the single canonical `owner/repo` key used by the authorization
guard, the GitHub API slug, the authorization error text, and the audit
record. The module owns policy only: two pure functions, no I/O, no config
access, no logging, and no dependency on any other `shared` module.

Usage:
    from shared.repo_identity import normalize_repo_key, is_canonical_repo_key

    key = normalize_repo_key("Owner", "Repo")      # "owner/repo"
    ok = is_canonical_repo_key("owner/repo")       # True
"""

from __future__ import annotations

__all__ = ["normalize_repo_key", "is_canonical_repo_key"]


def normalize_repo_key(owner: str, repo: str) -> str:
    """Return the canonical lowercase `owner/repo` key for the two parts.

    Raises ValueError when either part is not a string. Input that is already
    canonical is returned unchanged.
    """
    if not isinstance(owner, str) or not isinstance(repo, str):
        raise ValueError(
            f"repo identity parts must be str, got {type(owner).__name__} and {type(repo).__name__}"
        )
    return f"{owner.lower()}/{repo.lower()}"


def is_canonical_repo_key(entry: str) -> bool:
    """Report whether a stored allowlist entry is already in canonical form.

    Canonical form is `owner/repo` with exactly one separator, both parts
    non-empty, and no upper-case characters. The entry is not modified: a
    non-canonical entry is reported, never rewritten, so the guard can detect
    a non-canonical allowlist entry instead of silently matching nothing.
    Non-string input is reported as not canonical.
    """
    if not isinstance(entry, str):
        return False
    if entry.count("/") != 1:
        return False
    owner, repo = entry.split("/")
    if not owner or not repo:
        return False
    return entry == entry.lower()
