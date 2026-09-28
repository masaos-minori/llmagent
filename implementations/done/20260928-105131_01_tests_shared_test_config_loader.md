## Goal

Add unit test coverage for ADR-002's config isolation invariant enforced by `restrict_to()`, specifically testing basename extraction correctness in `_check_permission()` (REQ-003).

## Scope

- **In-Scope**: Adding test methods to `tests/shared/test_config_loader.py` asserting `_check_permission()` correctly handles paths with directory components via `Path(name).name`
- **Out-of-Scope**: Changes to `scripts/shared/config_loader.py`; updates to `docs/10_adr/adr-index.md` or `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

## Assumptions

- The existing `TestRestrictToIsolation` class provides sufficient baseline coverage for basic `restrict_to()` scenarios
- `ConfigPermissionError` exception type and message format are stable and can be relied upon in test assertions
- `_reset_for_testing()` is a test-only mechanism and does not need production-side changes

## Design decisions

- Extend `TestRestrictToIsolation` rather than creating a new class — keeps related tests together
- Use tmp_path fixture for isolated filesystem state per test
- Test both positive (authorized path with directory component) and negative (unauthorized path with directory component) cases

## Alternatives considered

- Creating a separate `TestBasenameExtraction` class — rejected because basename extraction is an internal detail of `_check_permission()`, not a public API boundary
- Testing via `load_all()` instead of `load()` — rejected because `load()` is the primary entry point and already covered by existing tests

## Implementation

### Target file

`tests/shared/test_config_loader.py`

### Procedure

Add two new test methods to `TestRestrictToIsolation`:
1. `test_restricted_load_with_directory_component_in_path` — verifies `Path(name).name` correctly extracts basenames from paths containing directory components
2. `test_exact_basename_matching_rejects_partial_matches` — ensures partial filename matches are rejected

### Method

1. Create a temporary directory with files: `subdir/a.toml`, `b_backup.toml`, `b.toml`
2. Call `ConfigLoader.restrict_to("a.toml")` to restrict loading to only `a.toml`
3. Verify that loading `"subdir/a.toml"` succeeds (basename extracted correctly)
4. Verify that loading `"b_backup.toml"` raises `ConfigPermissionError` (partial match rejection)

### Details

**Test 1: Basename extraction with directory components**

```python
def test_restricted_load_with_directory_component_in_path(self, tmp_path: Path) -> None:
    """Loading a file whose path contains directory components should succeed if the basename is authorized."""
    ConfigLoader.restrict_to("a.toml")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "a.toml").write_text("[section]\nfoo = 1\n")
    loader = ConfigLoader(config_dir=tmp_path)
    result = loader.load("subdir/a.toml")
    assert result["section"]["foo"] == 1
```

This test verifies that `_check_permission()`'s use of `Path(name).name` (line 120 of `config_loader.py`) correctly extracts the basename `"a.toml"` from the path `"subdir/a.toml"`, allowing the load to proceed.

**Test 2: Exact basename matching rejects partial matches**

```python
def test_exact_basename_matching_rejects_partial_matches(self, tmp_path: Path) -> None:
    """Partial filename matches must be rejected — 'a_backup.toml' must not match 'a.toml'."""
    ConfigLoader.restrict_to("a.toml")
    (tmp_path / "a_backup.toml").write_text("[section]\nbar = 2\n")
    loader = ConfigLoader(config_dir=tmp_path)
    with pytest.raises(ConfigPermissionError, match="not permitted"):
        loader.load("a_backup.toml")
```

This test verifies that the basename comparison in `_check_permission()` is exact — `"a_backup.toml"` must NOT match `"a.toml"` in the allowed set.

## Compatibility considerations

- No compatibility impact — adding tests does not change behavior
- Existing `TestRestrictToIsolation` tests remain valid and unaffected

## Security considerations

- This test directly validates a security-relevant invariant (config isolation)
- Ensures future changes cannot silently weaken the permission check

## Rollback considerations

- If the test fails after a code change, it indicates a regression in the permission check
- Revert the code change and re-run the test to confirm the fix

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_config_loader.py` | Unit test execution | `uv run pytest tests/shared/test_config_loader.py::TestRestrictToIsolation -v` | All new tests pass |
| `tests/shared/test_config_loader.py` | Full suite regression | `uv run pytest` | No regressions |

## Completion criteria

- [ ] New test `test_restricted_load_with_directory_component_in_path` exists and passes (REQ-003)
- [ ] New test `test_exact_basename_matching_rejects_partial_matches` exists and passes (REQ-001)
- [ ] Full test suite passes with no regression (REQ-001)

## Out of scope

- Documentation updates (`docs/10_adr/adr-index.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
- Production code changes (`scripts/shared/config_loader.py`)
- Tests for other requirements (REQ-002)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260928-155004 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260928-155004 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260928-155004 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260928-155004 | Out of scope: adr-index.md and governance_03 updates handled by companion _02/_03 docs. |

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
- **Requirement ID**: REQ-003 (basename extraction correctness); REQ-001 (exact basename matching)
- **Source issue**: issues/20260927-211337_ci009_add-unit-test-for-adr-002-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-085809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-105131
- **Related target files**: tests/shared/test_config_loader.py