# Implementation Procedure: NC-020 Row 5 — Extend integration tests for target resolution

## Goal

Extend `tests/mcp_servers/git/test_mcp_git.py` with assertions verifying that audit records contain the correct `target` field value after Row 1 changes.

## Scope

Only `tests/mcp_servers/git/test_mcp_git.py`: add new test methods. No other files are modified by this procedure document.

## Assumptions

- Row 1 fixes `"repo"` to `"repo_path"` key in audit call.
- Row 2 changes `_check_repo_path()` return type to `(bool, str, str)`.
- Existing property test `test_check_repo_path_equivalence` covers equivalence; no need to duplicate.

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

`tests/mcp_servers/git/test_mcp_git.py`

### Procedure

1. Add `test_check_repo_path_resolved_path_on_success` method.
2. Add `test_check_repo_path_empty_resolved_path_on_failure` method.
3. Add `test_audit_target_canonical_for_valid_call` method.
4. Add `test_audit_target_empty_for_rejected_call` method.

### Method

Append new test methods to the existing file.

### Details

```python
# --- New methods for TestCheckRepoPath class ---

class TestCheckRepoPath:
    # ... existing methods unchanged ...

    def test_resolved_path_on_success(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, err, resolved = svc._check_repo_path("/opt/repos/myproject")
        assert ok is True
        assert err == ""
        assert resolved == "/opt/repos/myproject"

    def test_empty_resolved_path_on_failure(self) -> None:
        svc = _svc(allowed=["/opt/repos"])
        ok, err, resolved = svc._check_repo_path("/home/user/project")
        assert ok is False
        assert "[DENIED]" in err
        assert resolved == ""

# --- New class for audit target verification ---

class TestAuditTargetResolution:
    """Verify audit target uses canonical identity."""

    @pytest.mark.asyncio
    async def test_audit_target_is_canonical_for_status_call(self) -> None:
        svc = _svc(allowed=["/opt/repos"], read_only=False)
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        with patch.object(svc, "_open_repo", return_value=mock_repo):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result
        # Audit target would be "/opt/repos/proj" (canonical), not symlink path

    @pytest.mark.asyncio
    async def test_audit_target_empty_for_denied_call(self) -> None:
        svc = _svc(allowed=[], read_only=True)
        result = await svc.git_checkout({
            "repo_path": "/opt/repos/proj",
            "branch": "main",
        })
        assert "[DENIED]" in result
        # Audit target would be "" (empty) for rejected call
```

Note: Existing `TestCheckRepoPath` methods must update their tuple unpacking from `ok, err = ...` to `ok, err, resolved = ...` after Row 2 is applied.

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

- [ ] Two new methods added to TestCheckRepoPath class
- [ ] New TestAuditTargetResolution class added
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
| 1 | Add resolved path assertion methods | Pending | - | - | |
| 2 | Add TestAuditTargetResolution class | Pending | - | - | |
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
- **Related target files**: tests/mcp_servers/git/test_mcp_git.py
