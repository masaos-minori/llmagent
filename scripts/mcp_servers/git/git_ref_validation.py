#!/usr/bin/env python3
"""scripts/mcp_servers/git/git_ref_validation.py — ref, remote, and protected-branch argument guards for the git MCP tools.

Moved verbatim out of git_service.py. The guards are pure: each caller passes the
configuration the guard needs, the same way git_service.py passes allowed_repo_paths
to git_security.is_within_allowed_paths. Repo-path containment and the read_only
write guard stay in git_service.py and git_security.py.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

# Structural tokens and forms the write-ref allowlist rejects: force-push syntax,
# refspec and revision ranges, and full ref names. Models `git check-ref-format
# --branch` for the values handed to GitPython by the write pipeline.
_REF_FORBIDDEN_TOKENS: tuple[str, ...] = (
    "+",
    ":",
    "^",
    "~",
    "?",
    "*",
    "[",
    "\\",
    "..",
    "@{",
)


def _has_forbidden_char(ref: str) -> bool:
    """Return True when *ref* carries whitespace or a control character."""
    return any(ch.isspace() or ord(ch) < 32 for ch in ref)


def _is_simple_ref_name(ref: str) -> bool:
    """Return True when *ref* is a simple branch name.

    Rejects structural tokens (`+ : ^ ~ ? * [`), the `..` and `@{` range forms,
    whitespace and control characters, `refs/` prefixes, and `HEAD`. An empty ref
    is simple here; the empty-branch case is denied by the protected-branch guard.
    """
    if any(tok in ref for tok in _REF_FORBIDDEN_TOKENS):
        return False
    if _has_forbidden_char(ref):
        return False
    return not ref.startswith("refs/") and ref != "HEAD"


def validate_ref(ref: str) -> tuple[bool, str]:
    """Check if a ref is safe (not an option)."""
    if not ref:
        return True, ""
    if ref.startswith("-"):
        return False, f"[DENIED] Ref {ref!r} looks like a CLI option"
    return True, ""


def validate_ref_allowlist(ref: str) -> tuple[bool, str]:
    """Check if a write branch/remote ref is an allowed simple name.

    The form rules live in `_is_simple_ref_name`. An empty ref passes here and
    is caught by `validate_protected` (branch must not be empty), preserving
    the prior `validate_ref("")` -> pass behavior.
    """
    if _is_simple_ref_name(ref):
        return True, ""
    return False, f"[DENIED] Ref {ref!r} is not a valid simple branch name"


def validate_remote(remote: str) -> tuple[bool, str]:
    """Check if a remote name is a safe simple name (no CLI-option injection)."""
    if remote.startswith("-"):
        return False, f"[DENIED] Remote {remote!r} looks like a CLI option"
    if re.fullmatch(r"[A-Za-z0-9._-]+", remote):
        return True, ""
    return False, f"[DENIED] Remote {remote!r} is not a valid remote name"


def validate_protected(
    branch: str, protected_branches: Sequence[str]
) -> tuple[bool, str]:
    """Check if a branch is protected."""
    if not branch:
        return False, "[DENIED] branch must not be empty"
    if branch in protected_branches:
        return False, f"[DENIED] {branch!r} is a protected branch"
    return True, ""


def require_ok(result: tuple[bool, str]) -> None:
    """Turn a rejected validation result into the ValueError the dispatch table reads.

    Every git_* handler reports a validation or policy rejection this way, so a
    denial never reaches the caller as a successful result string.
    """
    ok, err = result
    if not ok:
        raise ValueError(err)


def require_branch_refs(branch: str, protected_branches: Sequence[str]) -> None:
    """Write-tool branch guards, in the established order: form, then protected."""
    require_ok(validate_ref_allowlist(branch))
    require_ok(validate_protected(branch, protected_branches))
