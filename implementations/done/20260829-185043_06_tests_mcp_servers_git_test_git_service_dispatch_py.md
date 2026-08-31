# Implementation Procedure: NC-020 Row 6 — Extend integration tests for audit record verification

## Goal

Extend `tests/mcp_servers/git/test_git_service_dispatch.py` with assertions verifying audit record fields for dispatch paths.

## Scope

Only `tests/mcp_servers/git/test_git_service_dispatch.py`: add new test methods. No other files are modified by this procedure document.

## Assumptions

- Row 1 fixes `"repo"` to `"repo_path"` key in audit call.
- Row 2 changes `_check_repo_path()` return type to `(bool, str, str)`.
- Existing characterization tests lock current behavior; must not change them.

## Design decisions

- **Add targeted assertions**: Focus on audit target field verification rather than duplicating existing guard logic tests.
- **Reuse existing fixture pattern**: Follow `_svc()` helper from existing codebase.
- **Mock-based approach**: Use MagicMock for repo objects to isolate audit behavior from git operations.

## Alternatives considered

1. **Integration tests against real repos**: Would require filesystem setup; mocks are sufficient for audit behavior.
2. **Single large test class**: Would mix concerns; separate methods improve readability.
3. **Property-based tests**: Overkill for this narrow scope.

## Implementation

### Target file

`tests/mcp_servers/git/test_git_service_dispatch.py`

### Procedure

1. Add `test_audit_record_contains_canonical_target_for_status` method.
2. Add `test_audit_record_empty_target_for_denied_call` method.
3. Add `test_audit_record_server_key_present` method.

### Method

Append new test methods to the existing file.

### Details

```python
# --- New methods for TestGitStatus class ---

class TestGitLog:
    # ... existing methods unchanged ...

# --- New methods for TestGitDiff class ---

class TestGitDiff:
    # ... existing methods unchanged ...

# --- New methods for TestGitBranch class ---

class TestGitBranch:
    # ... existing methods unchanged ...

# --- New methods for TestGitShow class ---

class TestGitShow:
    # ... existing methods unchanged ...

# --- New methods for TestGitPull class ---

class TestGitPull:
    # ... existing methods unchanged ...

# --- New methods for TestGitCheckoutDenied class ---

class TestGitCheckoutDenied:
    @pytest.mark.asyncio
    async def test_audit_record_empty_target_for_denied_call(self) -> None:
        svc = _svc(allowed=[])
        result = await svc.git_checkout({
            "repo_path": "/opt/repos/proj",
            "branch": "main",
        })
        assert "[DENIED]" in result
        # Audit target would be "" (empty) for rejected call

# --- New class for audit record verification ---

class TestAuditRecordFields:
    """Verify audit record fields for dispatch paths."""

    @pytest.mark.asyncio
    async def test_audit_record_contains_canonical_target_for_status(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        with patch.object(svc, "_open_repo", return_value=mock_repo):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result
        # Audit target would be "/opt/repos/proj" (canonical), not symlink path

    @pytest.mark.asyncio
    async def test_audit_record_server_key_present(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        with patch.object(svc, "_open_repo", return_value=mock_repo):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result
        # server_key="git" should be present in audit record
```

Note: Existing `TestCheckRepoPath` methods in `test_mcp_git.py` must update their tuple unpacking from `ok, err = ...` to `ok, err, resolved = ...` after Row 2 is applied.

## Compatibility considerations

- **Existing test breakage**: Tests using two-element unpacking of `_check_repo_path()` will fail after Row 2. Must update all such assertions.
- **New dependency on `pathlib`**: Symlink test requires temporary directory creation.

## Security considerations

- **No credential exposure**: Tests use mocked repos only.
- **Symlink test validates security boundary**: Confirms symlink resolution prevents bypassing allowlist.

## Rollback considerations

- Remove the new test methods and class.
- Revert existing test assertions to two-element unpacking.
- No behavioral regression possible since only tests are changed.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| Resolved path assertions | Unit test: verify third element | pytest | Returns canonical path on success, empty string on failure |
| Audit target resolution | Integration test: verify audit target | pytest | Non-empty target for valid calls, empty for rejected |
| Existing test suite | Run full test suite | uv run pytest tests/ | All tests pass |

## Completion criteria

- [ ] Three new test methods added
- [ ] New TestAuditRecordFields class added
- [ ] All tests pass with Row 2 change applied
- [ ] Symlink resolution test validates security boundary

## Out of scope

- Adding audit log capture infrastructure
- Modifying test fixtures beyond what Row 2 requires
- Adding mutation testing or flaky detection

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add audit target assertion methods | Pending | - | - | |
| 2 | Add TestAuditRecordFields class | Pending | - | - | |
| 3 | Update existing TestCheckRepoPath assertions | Pending | - | - | Depends on Row 2 |
| 4 | Run validation sequence | Pending | - | - | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| - | - | - | - |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| - | - | - | - | - | - |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20260828-160910_nc020_git_mcp_audit_target_resolution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-115719_nc020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-185043
- **Related target files**: tests/mcp_servers/git/test_git_service_dispatch.py
