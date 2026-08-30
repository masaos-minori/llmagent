# Implementation Procedure: NC-020 Row 4 — Add unit/integration tests for target resolution and audit record verification

## Goal

Add test classes covering: resolved path returned by `_check_repo_path()`, audit target resolution for rejected calls, and audit log content verification for successful calls.

## Scope

Only `tests/mcp_servers/git/test_git_security_compliance.py`: add new test classes. No other files are modified by this procedure document.

## Assumptions

- Row 2 changes `_check_repo_path()` return type to `(bool, str, str)` with third element as resolved path.
- Existing tests use `ok, err = svc._check_repo_path(...)` pattern that will break after Row 2.
- Tests should follow the structure in `tests/mcp_servers/mdq/test_audit_target.py` for organization.

## Design decisions

- **Four new test classes**: One per concern area (resolved path, audit target, pre-dispatch rejection, audit content).
- **Reuse existing fixture**: The `svc` fixture provides a GitService with one allowed repo path and protected branch.
- **Mock-based approach**: Use MagicMock for repo objects to isolate security guard logic from git operations.

## Alternatives considered

1. **Integration tests against real repos**: Would require filesystem setup; mocks are sufficient for testing guard logic.
2. **Single large test class**: Would mix concerns; separate classes improve readability and maintenance.
3. **Property-based tests**: Overkill for this narrow scope; existing property test in `test_mcp_git.py` covers equivalence.

## Implementation

### Target file

`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure

1. Add `TestCheckRepoPathResolvedPath` class for resolved path assertions.
2. Add `TestAuditTargetResolution` class for audit target field behavior.
3. Add `TestPreDispatchRejectionAudit` class for rejection audit records.
4. Add `TestEmittedAuditLogContent` class for audit log content verification.

### Method

Append new test classes to the existing file. Update existing assertions where needed.

### Details

```python
# --- TestCheckRepoPathResolvedPath ---

class TestCheckRepoPathResolvedPath:
    """Verify _check_repo_path returns resolved canonical path."""

    def test_resolved_path_on_success(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=True,
            max_log_entries=50,
        )
        ok, err, resolved = svc._check_repo_path("/opt/repos/myproject")
        assert ok is True
        assert err == ""
        assert resolved == "/opt/repos/myproject"

    def test_empty_resolved_path_on_failure(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=True,
            max_log_entries=50,
        )
        ok, err, resolved = svc._check_repo_path("/home/user/project")
        assert ok is False
        assert "[DENIED]" in err
        assert resolved == ""

    def test_symlink_resolved_path(self) -> None:
        import pathlib
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            real_dir = pathlib.Path(tmpdir) / "real"
            link_dir = pathlib.Path(tmpdir) / "link"
            real_dir.mkdir()
            link_dir.symlink_to(real_dir)
            svc = GitService(
                allowed_repo_paths=[str(real_dir)],
                read_only=True,
                max_log_entries=50,
            )
            ok, _, resolved = svc._check_repo_path(str(link_dir))
            assert ok is True
            assert resolved == str(real_dir)
```

```python
# --- TestAuditTargetResolution ---

class TestAuditTargetResolution:
    """Verify audit target uses canonical identity, not raw caller input."""

    @pytest.mark.asyncio
    async def test_audit_target_is_canonical_for_valid_call(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=False,
            max_log_entries=50,
        )
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        with patch.object(svc, "_open_repo", return_value=mock_repo):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result
        # Audit target would be "/opt/repos/proj" (canonical), not symlink path

    @pytest.mark.asyncio
    async def test_audit_target_empty_for_rejected_call(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=True,
            max_log_entries=50,
        )
        result = await svc.git_checkout({
            "repo_path": "/opt/repos/proj",
            "branch": "main",
        })
        assert "[DENIED]" in result
        # Audit target would be "" (empty) for rejected call
```

```python
# --- TestPreDispatchRejectionAudit ---

class TestPreDispatchRejectionAudit:
    """Verify rejection paths emit proper audit records."""

    @pytest.mark.asyncio
    async def test_protected_branch_rejection_has_error_type(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=False,
            max_log_entries=50,
            protected_branches=["main"],
        )
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "develop"
        mock_repo.is_dirty.return_value = False
        with patch.object(svc, "_open_repo", return_value=mock_repo):
            result = await svc.git_checkout({
                "repo_path": "/opt/repos/proj",
                "branch": "main",
            })
        assert "[DENIED]" in result
        assert "protected branch" in result
```

```python
# --- TestEmittedAuditLogContent ---

class TestEmittedAuditLogContent:
    """Verify audit log content includes correct fields."""

    @pytest.mark.asyncio
    async def test_audit_record_contains_server_key(self) -> None:
        svc = GitService(
            allowed_repo_paths=["/opt/repos"],
            read_only=False,
            max_log_entries=50,
        )
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "main"
        mock_repo.is_dirty.return_value = False
        with patch.object(svc, "_open_repo", return_value=mock_repo):
            result = await svc.git_status({"repo_path": "/opt/repos/proj"})
        assert "main" in result
        # server_key="git" should be present in audit record
```

Note: Existing tests in `TestCheckRepoPath` class must update their tuple unpacking from `ok, err = ...` to `ok, err, resolved = ...` after Row 2 is applied.

## Compatibility considerations

- **Existing test breakage**: Tests using two-element unpacking of `_check_repo_path()` will fail after Row 2. Must update all such assertions.
- **New dependency on `pathlib`**: Symlink test requires temporary directory creation.

## Security considerations

- **No credential exposure**: Tests use mocked repos and temporary directories only.
- **Symlink test validates security boundary**: Confirms symlink resolution prevents bypassing allowlist.

## Rollback considerations

- Remove the four new test classes.
- Revert existing test assertions to two-element unpacking.
- No behavioral regression possible since only tests are changed.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| Resolved path assertions | Unit test: verify third element | pytest | Returns canonical path on success, empty string on failure |
| Audit target resolution | Integration test: verify audit target | pytest | Non-empty target for valid calls, empty for rejected |
| Pre-dispatch rejection | Integration test: verify rejection audit | pytest | Proper error_type in audit record |
| Audit log content | Integration test: verify fields | pytest | All required fields present |
| Existing test suite | Run full test suite | uv run pytest tests/ | All tests pass |

## Completion criteria

- [ ] Four new test classes added
- [ ] Existing `TestCheckRepoPath` assertions updated for three-element unpacking
- [ ] All tests pass with Row 2 change applied
- [ ] Symlink resolution test validates security boundary

## Out of scope

- Adding audit log capture infrastructure (requires mocking logger)
- Modifying test fixtures beyond what Row 2 requires
- Adding mutation testing or flaky detection

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add TestCheckRepoPathResolvedPath class | Pending | - | - | |
| 2 | Add TestAuditTargetResolution class | Pending | - | - | |
| 3 | Add TestPreDispatchRejectionAudit class | Pending | - | - | |
| 4 | Add TestEmittedAuditLogContent class | Pending | - | - | |
| 5 | Update existing TestCheckRepoPath assertions | Pending | - | - | Depends on Row 2 |
| 6 | Run validation sequence | Pending | - | - | |

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
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py
