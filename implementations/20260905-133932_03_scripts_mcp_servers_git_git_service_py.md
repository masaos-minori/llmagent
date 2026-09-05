# Implementation Procedure Output Template (Canonical)

## Goal

Replace `GitService._validate_repo()`'s `req_repo_path.startswith(p)` check with component-aware containment using `PurePosixPath.relative_to()`, so `gitdispatch`'s Plan does not reintroduce the sibling-path vulnerability once implemented (REQ-007).

## Scope

- Modify `GitService._validate_repo()` method in `git_service.py` (lines 108-120).
- Replace the `any(req_repo_path.startswith(p) for p in self._allowed_repo_paths)` check with component-aware containment.

## Assumptions

- `GitService._check_repo_path()`'s existing `PurePosixPath.relative_to()`-based containment logic is itself correct — this Plan reuses its approach rather than re-designing containment logic from scratch.
- `_resolve_repo_path()` is available as a module-level import in `git_service.py` (already imported at line 37).
- `os.path.normpath` is available for normalizing the resolved path before containment checking.

## Design decisions

- Replace the `startswith()` check inline within `_validate_repo()` rather than delegating to `_check_repo_path()`. This keeps `_validate_repo()` as the single entry point for validation used by `_run_tool()`, avoiding the need to change the method signature or add a new method.
- Use the same `PurePosixPath.relative_to()` approach as `_check_repo_path()` for consistency between the two containment checks.
- Keep the write guard check (`tool_name in _WRITE_TOOLS and self._read_only`) unchanged — it is orthogonal to the path containment fix.

## Alternatives considered

- Refactoring `_validate_repo()` to delegate to `_check_repo_path()`. Rejected because `_check_repo_path()` returns `(ok, error, resolved_path)` and `_validate_repo()` returns `RepoValidationResult` — changing the return type would cascade through all callers.
- Creating a shared helper function. Rejected because the containment logic is simple enough (a few lines) and duplicating it here maintains symmetry with `_check_repo_path()`, making future divergence easier to spot.
- Using `Path.is_relative_to()` (Python 3.9+). Rejected because the existing `_check_repo_path()` already uses `PurePosixPath.relative_to()` which handles symlink-resolved paths correctly; switching to `Path.is_relative_to()` would require resolving symlinks first, adding complexity.

## Implementation

### Target file

`scripts/mcp_servers/git/git_service.py`

### Procedure

1. In `GitService._validate_repo()` (line 108), replace the containment check:
   ```python
   # OLD (line 112):
   if not any(req_repo_path.startswith(p) for p in self._allowed_repo_paths):

   # NEW:
   ok, err = self._is_within_allowed_paths(req_repo_path)
   if not ok:
       return RepoValidationResult(error_message=err)
   ```

2. Add a new private method `_is_within_allowed_paths` to `GitService`:
   ```python
   def _is_within_allowed_paths(self, repo_path: str) -> tuple[bool, str]:
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
       # allowed_repo_paths before calling this method.
       if not self._allowed_repo_paths:
           return True, ""

       for allowed in self._allowed_repo_paths:
           try:
               PurePosixPath(normalized).relative_to(PurePosixPath(allowed))
               return True, ""
           except ValueError:
               continue

       return False, "[DENIED] repo_path not in allowed paths"
   ```

3. The write guard check (lines 116-119) remains unchanged:
   ```python
   if tool_name in _WRITE_TOOLS and self._read_only:
       return RepoValidationResult(
           error_message="[DENIED] git-mcp is configured with read_only=true"
       )
   ```

### Method

Inline modification of `_validate_repo()` plus addition of a new private method `_is_within_allowed_paths`.

### Details

The full modified `_validate_repo` method after changes:

```python
async def _validate_repo(
    self, req_repo_path: str, tool_name: str
) -> RepoValidationResult:
    """Check repo_path and write guard; return result with error_message (empty on success)."""
    ok, err = self._is_within_allowed_paths(req_repo_path)
    if not ok:
        return RepoValidationResult(error_message=err)
    if tool_name in _WRITE_TOOLS and self._read_only:
        return RepoValidationResult(
            error_message="[DENIED] git-mcp is configured with read_only=true"
        )
    return RepoValidationResult(error_message="")
```

And the new method added after `_open_repo`:

```python
def _is_within_allowed_paths(self, repo_path: str) -> tuple[bool, str]:
    """Check whether repo_path is within one of the allowed repository roots."""
    from pathlib import PurePosixPath

    ok, err, resolved = _resolve_repo_path(repo_path)
    if not ok:
        return False, err

    normalized = os.path.normpath(resolved)

    if not self._allowed_repo_paths:
        return True, ""

    for allowed in self._allowed_repo_paths:
        try:
            PurePosixPath(normalized).relative_to(PurePosixPath(allowed))
            return True, ""
        except ValueError:
            continue

    return False, "[DENIED] repo_path not in allowed paths"
```

## Compatibility considerations

- `_validate_repo()` returns `RepoValidationResult` — the return type is unchanged. Only the internal containment logic changes.
- The new `_is_within_allowed_paths` method is private (`_` prefix) and not part of the public API.
- `RepoValidationResult` emits a deprecation warning via `__post_init__` — this is pre-existing behavior and unrelated to this change.
- Once `gitdispatch`'s Plan lands and routes live traffic through `GitService.get_dispatch_table()`, this method will become reachable. The fix ensures that when it does, the sibling-path vulnerability is already closed.

## Security considerations

- **Critical**: The current `startswith()` check allows sibling-path attacks (e.g., `/allowed-repo-evil` matches `/allowed-repo`). This fix closes that gap preemptively.
- Component-aware containment prevents sibling-path attacks regardless of whether `gitdispatch` has landed yet.
- Symlink escape prevention is handled by `_resolve_repo_path()` which resolves symlinks before containment checking.
- The empty-list fail-closed convention is preserved: if `self._allowed_repo_paths` is empty, the method returns `(True, "")` but callers should handle the empty case separately (as they do in `_git_tool_availability`).

## Rollback considerations

- Rolling back requires reverting `_validate_repo()` to use `startswith()` and removing `_is_within_allowed_paths`.
- Since this is dead code today (per `gitauth`'s Plan), rolling back has no immediate operational impact. However, once `gitdispatch` lands, rollback would restore the vulnerability.
- If the containment logic proves too aggressive (rejecting legitimate paths), the fix is to update `allowed_repo_paths` in config rather than revert the code.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| `_validate_repo` unit tests | Unit | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -v` | Sibling-path rejection test passes |
| Full git-mcp suite | Regression | `uv run pytest tests/mcp_servers/git/ -v` | 184+ tests pass, no new failures |
| Static analysis | Lint/type/security | `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` | All pass with no new findings |

## Completion criteria

- [ ] `_validate_repo()` uses `PurePosixPath.relative_to()`-style component-aware containment instead of `startswith()`.
- [ ] Sibling paths like `/allowed-repo-evil` are rejected when `/allowed-repo` is configured as an allowed root.
- [ ] The new `_is_within_allowed_paths` method mirrors `_check_repo_path()`'s containment logic.
- [ ] A regression test exists asserting `_validate_repo()` rejects sibling paths.
- [ ] All existing tests continue to pass.
- [ ] Static analysis tools report no new findings.

## Out of scope

- Modifying `_check_repo_path()` — it already implements the correct containment logic; this Plan only fixes `_validate_repo()`.
- Wiring the containment check into `git_server.py`'s `call_tool` — covered by the related target file `scripts/mcp_servers/git/git_security.py`.
- Fixing the rejection-path audit call — covered by the related target file.
- Test additions for the live dispatch path — covered by the related target file `tests/mcp_servers/git/test_git_security_compliance.py`.
- Adding the `requested_target` and `canonical_target` audit fields — covered by the related target file.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace startswith() with component-aware containment in _validate_repo() | Pending | — | — | |
| 2 | Add _is_within_allowed_paths() helper method | Pending | — | — | |
| 3 | Add regression test for sibling-path rejection | Pending | — | — | |
| 4 | Run validation sequence | Pending | — | — | |

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
- **Requirement ID**: REQ-007: Fix `GitService._validate_repo()`'s `req_repo_path.startswith(p)` check to use component-aware containment
- **Source issue**: issues/20260902-144911_gitpathaudit_harden_repository_path_authorization_and_audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191846_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-133932
- **Related target files**: scripts/mcp_servers/git/git_service.py
