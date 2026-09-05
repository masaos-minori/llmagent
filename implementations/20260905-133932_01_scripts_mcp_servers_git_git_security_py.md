# Implementation Procedure Output Template (Canonical)

## Goal

Add path-component-aware `allowed_repo_paths` containment checking (`PurePosixPath.relative_to()`-style) to the live dispatch path, reusing `GitService._check_repo_path()`'s existing correct logic (REQ-001, REQ-002).

## Scope

- Extend `_resolve_repo_path()` or add a sibling function in `git_security.py` that takes `allowed_repo_paths` as a parameter and performs component-aware containment checking.
- The new containment check must reject sibling paths like `/allowed-repo-evil` for an `/allowed-repo` root.

## Assumptions

- `GitService._check_repo_path()`'s existing `PurePosixPath.relative_to()`-based containment logic is itself correct — this Plan reuses its approach rather than re-designing containment logic from scratch.
- `config/git_mcp_server.toml`'s `allowed_repo_paths` field and its empty-list-means-deny-all convention are the correct policy surface — this Plan makes that policy actually enforced, it does not change what the policy says.

## Design decisions

- Add a standalone function `is_within_allowed_paths(repo_path: str, allowed_repo_paths: list[str]) -> tuple[bool, str]` that mirrors `GitService._check_repo_path()`'s logic, rather than modifying `_resolve_repo_path()` directly. This keeps `_resolve_repo_path()` as a pure canonicalizer and separates concerns.
- The function returns `(ok, error)` where `ok=True` means the path passes containment, and `error` contains the denial reason.
- Import `PurePosixPath` inside the function to avoid adding a module-level import dependency in `git_security.py`.

## Alternatives considered

- Modifying `_resolve_repo_path()` to accept `allowed_repo_paths` and perform containment inline. Rejected because it would couple path resolution with authorization logic, violating separation of concerns.
- Adding containment as a method on `GitSecurityGuards`. Rejected because the live dispatch path in `git_server.py` currently calls `_resolve_repo_path()` as a module-level function, not through a guard instance. A standalone function is the minimal integration point.

## Implementation

### Target file

`scripts/mcp_servers/git/git_security.py`

### Procedure

1. Add a new module-level function `is_within_allowed_paths(repo_path: str, allowed_repo_paths: list[str]) -> tuple[bool, str]` after `_resolve_repo_path()`.
2. In the function body, first call `_resolve_repo_path(repo_path)` to get the canonical path. If resolution fails, return `(False, err)`.
3. If `allowed_repo_paths` is empty, return `(True, "")` — the fail-closed-empty-list convention means callers should handle the empty case separately (as they already do in `_git_tool_availability`).
4. For each allowed path, attempt `PurePosixPath(normalized_resolved).relative_to(PurePosixPath(allowed))`. If any succeeds, return `(True, "")`.
5. If none succeed, return `(False, "[DENIED] repo_path not in allowed paths")`.

### Method

Module-level function addition.

### Details

```python
def is_within_allowed_paths(repo_path: str, allowed_repo_paths: list[str]) -> tuple[bool, str]:
    """Check whether repo_path is within one of the allowed repository roots.

    Uses PurePosixPath.relative_to() for component-aware containment,
    rejecting sibling paths like /allowed-repo-evil for an /allowed-repo root.
    Returns (ok, error) where ok=True means the path is authorized.
    """
    from pathlib import PurePosixPath

    ok, err, resolved = _resolve_repo_path(repo_path)
    if not ok:
        return False, err

    normalized = os.path.normpath(resolved)

    # Fail-closed-empty-list convention: callers must enforce non-empty
    # allowed_repo_paths before calling this function.
    if not allowed_repo_paths:
        return True, ""

    for allowed in allowed_repo_paths:
        try:
            PurePosixPath(normalized).relative_to(PurePosixPath(allowed))
            return True, ""
        except ValueError:
            continue

    return False, "[DENIED] repo_path not in allowed paths"
```

The function needs `import os` added at the top of the file (for `os.path.normpath`).

## Compatibility considerations

- No backward-compatible public API changes. The new function is internal to the git-mcp module.
- `GitService._check_repo_path()` already implements the same logic; this function provides the same behavior for the live dispatch path. Once implemented, both code paths will agree on containment semantics.
- The function signature matches the pattern used elsewhere in the codebase (e.g., `_resolve_repo_path` returns `tuple[bool, str, str]`; this returns `tuple[bool, str]` since the caller already has the resolved path from `_resolve_repo_path`).

## Security considerations

- **Critical**: The current codebase has zero containment enforcement on the live dispatch path. Any resolvable filesystem path reaches `RepositoryState.snapshot()` and full tool execution regardless of `allowed_repo_paths`. This fix closes a live, exploitable gap.
- Component-aware containment prevents sibling-path attacks (e.g., `/allowed-repo-evil` matching `/allowed-repo`).
- Symlink escape prevention is handled by `_resolve_repo_path()` which resolves symlinks before containment checking.
- The function must be called from `git_server.py`'s `call_tool` before any `RepositoryState.snapshot()` call.

## Rollback considerations

- The new function is additive only — no existing code is modified. Rolling back requires removing the function and ensuring `git_server.py` does not call it.
- Since `git_server.py` must also be updated to call this function, rollback of just `git_security.py` without rolling back `git_server.py` is safe (the function simply becomes unused).
- If the containment logic proves too aggressive (rejecting legitimate paths), the fix is to update `allowed_repo_paths` in config, not revert the code.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| `is_within_allowed_paths` unit tests | Unit | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | Containment tests pass |
| Integration with `git_server.py` | Integration | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | Sibling-path rejection works end-to-end |
| Full git-mcp suite | Regression | `uv run pytest tests/mcp_servers/git/ -v` | 184+ tests pass, no new failures |
| Static analysis | Lint/type/security | `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` | All pass with no new findings |

## Completion criteria

- [ ] `is_within_allowed_paths()` is defined in `git_security.py` and uses `PurePosixPath.relative_to()` for component-aware containment.
- [ ] Sibling paths like `/allowed-repo-evil` are rejected when `/allowed-repo` is configured as an allowed root.
- [ ] The function is callable from the live dispatch path (integration verified via test, not yet wired into `git_server.py` — see related target file).
- [ ] All existing tests continue to pass.
- [ ] Static analysis tools report no new findings.

## Out of scope

- Wiring the containment check into `git_server.py`'s `call_tool` — covered by the related target file `scripts/mcp_servers/git/git_server.py`.
- Fixing the rejection-path audit call — covered by the related target file.
- Redacted vs. canonical audit target fields — covered by the related target file.
- Wrapping audit calls against propagating exceptions — covered by the related target file.
- Fixing `GitService._validate_repo()`'s vulnerable `startswith()` check — covered by the related target file `scripts/mcp_servers/git/git_service.py`.
- Test additions for the live dispatch path — covered by the related target file `tests/mcp_servers/git/test_git_security_compliance.py`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `is_within_allowed_paths()` in git_security.py | Pending | — | — | |
| 2 | Add unit tests for the new function | Pending | — | — | |
| 3 | Run validation sequence | Pending | — | — | |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001: Add path-component-aware `allowed_repo_paths` containment checking; REQ-002: Use `PurePosixPath.relative_to()`-style component-aware containment
- **Source issue**: issues/20260902-144911_gitpathaudit_harden_repository_path_authorization_and_audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191846_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-133932
- **Related target files**: scripts/mcp_servers/git/git_security.py
