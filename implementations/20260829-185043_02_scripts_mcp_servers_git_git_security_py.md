# Implementation Procedure: NC-020 Row 2 — Modify `_check_repo_path()` to expose resolved path

## Goal

Expose the resolved canonical repository path alongside the existing `(bool, str)` return value of `GitSecurityGuards._check_repo_path()`, enabling `call_tool()` to use the post-validation identity as the audit log `target` field instead of the raw caller string.

## Scope

Only `scripts/mcp_servers/git/git_security.py`: change `_check_repo_path()` signature and all callers' handling of its return value. No other files are modified by this procedure document.

## Assumptions

- All callers currently unpack the return value as `ok, err = _check_repo_path(...)`. After this change they must unpack as `ok, err, resolved = _check_repo_path(...)`.
- When `ok=False`, `resolved` should be an empty string `""` (no canonical identity exists on validation failure).
- When `ok=True`, `resolved` is `str(Path(repo_path).resolve())` — the absolute, symlink-resolved path.
- The existing `_repo_denied_msg()` helper is used only for the error string; it is not changed.

## Design decisions

- **Return type change**: `(bool, str) → (bool, str, str)`. The third element is the resolved path when `ok=True`, empty string when `ok=False`. This is minimal and non-breaking for callers that already handle the two-element case via tuple unpacking — they simply get one extra element.
- **Empty string on failure**: Using `""` rather than `None` avoids adding `Optional[str]` to the type signature, keeping the contract simple: callers always get a `str` for the third element.
- **No new public API**: `_check_repo_path()` remains private (underscore-prefixed). The change is internal to the security guard module.

## Alternatives considered

1. **Named tuple / dataclass return**: Would make the three elements more explicit (`ok`, `error`, `resolved_path`) but adds unnecessary boilerplate for a single-call-site consumer (`call_tool`). The positional tuple is sufficient given the small scope.
2. **Separate method `get_resolved_path()`**: Would avoid changing the existing return type but would require callers to invoke two methods, increasing complexity and potential inconsistency between the two calls.
3. **Keep returning `(bool, str)` and resolve path separately in `call_tool()`**: Would duplicate the `Path(repo_path).resolve()` computation that `_check_repo_path()` already performs, violating DRY.

## Implementation

### Target file

`scripts/mcp_servers/git/git_security.py`

### Procedure

1. Change `_check_repo_path()` return type annotation from `tuple[bool, str]` to `tuple[bool, str, str]`.
2. On success path (line 44-45), return `(True, "", str(target))` instead of `(True, "")`.
3. On failure paths (lines 41, 46), return `(False, <error>, "")` instead of `(False, <error>)`.
4. Update docstring to document the third element.

### Method

Direct modification of the `_check_repo_path()` method body and type annotation.

### Details

```python
# Before (current):
def _check_repo_path(self, repo_path: str) -> tuple[bool, str]:
    """Return (ok, error); ok=True when repo_path is within an allowed path prefix."""
    if not self._allowed:
        return False, _repo_denied_msg(repo_path)
    target = Path(repo_path).resolve()
    for allowed in self._allowed:
        if target.is_relative_to(allowed):
            return True, ""
    return False, _repo_denied_msg(repo_path)

# After:
def _check_repo_path(self, repo_path: str) -> tuple[bool, str, str]:
    """Return (ok, error, resolved_path).
    
    ok=True when repo_path is within an allowed path prefix.
    resolved_path is the canonical identity (empty string when ok=False).
    """
    if not self._allowed:
        return False, _repo_denied_msg(repo_path), ""
    target = Path(repo_path).resolve()
    for allowed in self._allowed:
        if target.is_relative_to(allowed):
            return True, "", str(target)
    return False, _repo_denied_msg(repo_path), ""
```

## Compatibility considerations

- **All callers must update their tuple unpacking**. Currently there are callers in:
  - `git_service.py` — uses `_check_repo_path()` in dispatch logic
  - Tests in `test_git_security_compliance.py` — mock and assert on return values
- **Type-checking impact**: Any code that relies on the old two-element unpacking pattern will fail at runtime with `ValueError: too many values to unpack`. Static type checkers will also flag mismatches.
- **Test compatibility**: Existing tests that assert on `(True, "")` or `(False, "message")` patterns will need updating to expect the third element.

## Security considerations

- **No credential exposure**: The resolved path is a filesystem path, never a remote URL. No credential material is introduced.
- **Symlink resolution preserved**: `Path(repo_path).resolve()` already resolves symlinks; the exposed value maintains this property.
- **Denial messages unchanged**: Error strings remain identical; only the return structure changes.

## Rollback considerations

- Revert the return type annotation and all three return statements to their original forms.
- Restore the original docstring.
- Update all callers back to two-element unpacking.
- Risk: If any caller fails to update unpacking during rollback, runtime errors will occur. Ensure all callers are reverted atomically.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| `_check_repo_path()` direct call | Unit test: verify resolved path returned on success, empty string on failure | pytest | Returns `(True, "", "/canonical/path")` for valid input; `(False, "DENIED", "")` for invalid |
| Callers updated | Integration test: verify callers correctly unpack three elements | pytest | No `ValueError: too many values to unpack`; audit records contain canonical target |
| Test suite | Run existing test suite | `uv run pytest tests/` | All tests pass with updated assertions |

## Completion criteria

- [ ] `_check_repo_path()` signature changed to `tuple[bool, str, str]`
- [ ] Success path returns `(True, "", str(target))`
- [ ] Failure paths return `(False, <error>, "")`
- [ ] Docstring updated to document third element
- [ ] All callers updated to unpack three elements
- [ ] Existing tests updated and passing

## Out of scope

- Modifying `call_tool()` to consume the new third element (covered by Row 1 procedure document)
- Adding new security guards or validation logic
- Changing `_repo_denied_msg()` output format
- Modifying `_check_write()` or other guard methods

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Modify `_check_repo_path()` return type and all return statements | Pending | — | — | |
| 2 | Update all callers to unpack three elements | Pending | — | — | |
| 3 | Update tests to match new return structure | Pending | — | — | |
| 4 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260828-160910_nc020_git_mcp_audit_target_resolution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-115719_nc020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-185043
- **Related target files**: scripts/mcp_servers/git/git_security.py
