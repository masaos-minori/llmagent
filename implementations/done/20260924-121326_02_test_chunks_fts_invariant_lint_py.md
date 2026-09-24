# Implementation Procedure: Test chunks_fts Invariant Lint Regression

## Goal

Create a regression test at `tests/test_chunks_fts_invariant_lint.py` that demonstrates an unsanctioned direct `chunks_fts` write is detected by the lint script, per REQ-06.

## Scope

- Create `tests/test_chunks_fts_invariant_lint.py` as a new file
- The test creates a temporary Python file containing an unsanctioned `INSERT INTO chunks_fts` statement
- Runs the lint script against the temp file
- Asserts that the script returns exit code 1 and reports the violation
- Cleans up the temp file

## Assumptions

- pytest is available for running tests
- The lint script exists at `tools/check_chunks_fts_invariant.py` (created by the companion implementation procedure)
- Temporary files are created in `pytest`'s `tmp_path` fixture and cleaned up automatically

## Design decisions

- Use `pytest.tmp_path` fixture for temporary file creation — automatic cleanup, no manual teardown needed
- Test three scenarios:
  1. Violation detection (positive test)
  2. Zero findings on sanctioned path (negative test)
  3. Zero findings on MDQ files (negative test)

## Alternatives considered

- **Subprocess vs. import**: Using `subprocess.run()` to invoke the script rather than importing it directly. This ensures the test validates the actual CLI behavior (exit codes, stdout output).
- **Temp file vs. mock**: Using a real temp file rather than mocking `rg`. This validates end-to-end behavior including subprocess invocation.

## Implementation

### Target file

`tests/test_chunks_fts_invariant_lint.py`

### Procedure

1. Create the test file with module docstring following project conventions
2. Implement `test_violation_detected(tmp_path)` — positive test
3. Implement `test_zero_findings_on_sanctioned_path(tmp_path)` — negative test
4. Implement `test_zero_findings_on_mdq_files(tmp_path)` — negative test

### Method

**Step 1: Module setup**

```python
"""Regression tests for tools/check_chunks_fts_invariant.py."""

import os
import subprocess
from pathlib import Path

import pytest

LINT_SCRIPT = Path("tools/check_chunks_fts_invariant.py")
```

**Step 2: Positive test — violation detection**

```python
def test_violation_detected(tmp_path: Path) -> None:
    """Verify the lint script detects an unsanctioned chunks_fts INSERT."""
    # Create a synthetic file with an unsanctioned write
    bad_file = tmp_path / "bad_script.py"
    bad_file.write_text(
        'db.execute("INSERT INTO chunks_fts(rowid, content) VALUES(?, ?)")\n'
    )
    
    result = subprocess.run(
        ["uv", "run", "python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True, text=True,
    )
    
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
    assert "bad_script.py" in result.stdout, f"Expected violation report in output: {result.stdout}"
```

**Step 3: Negative test — sanctioned path**

```python
def test_zero_findings_on_sanctioned_path(tmp_path: Path) -> None:
    """Verify the lint script produces zero findings on sanctioned write paths."""
    # Copy rag_maintenance_service.py's rebuild_fts to temp dir
    src = Path("scripts/agent/services/rag_maintenance_service.py")
    dst = tmp_path / "rag_maintenance_service.py"
    dst.write_text(src.read_text())
    
    result = subprocess.run(
        ["uv", "run", "python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True, text=True,
    )
    
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
    assert result.stdout.strip() == "", f"Expected no output, got: {result.stdout}"
```

**Step 4: Negative test — MDQ files**

```python
def test_zero_findings_on_mdq_files(tmp_path: Path) -> None:
    """Verify the lint script produces zero findings on MDQ files."""
    # Copy mdq/db_schema.py to temp dir (preserving directory structure)
    mdq_src = Path("scripts/mcp_servers/mdq/db_schema.py")
    mdq_dst = tmp_path / "mdq" / "db_schema.py"
    mdq_dst.parent.mkdir(parents=True, exist_ok=True)
    mdq_dst.write_text(mdq_src.read_text())
    
    result = subprocess.run(
        ["uv", "run", "python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True, text=True,
    )
    
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
    assert result.stdout.strip() == "", f"Expected no output, got: {result.stdout}"
```

### Details

- **REQ-06**: Test demonstrates that an unsanctioned direct `chunks_fts` write is detected by the lint script
- **T-01**: Lint script correctly identifies unsanctioned `chunks_fts` INSERT/UPDATE in a synthetic Python file
- **T-02**: Lint script produces zero findings on the two sanctioned write paths
- **T-03**: Lint script produces zero findings on MDQ files

## Compatibility considerations

- Requires `rg` to be installed (same dependency as the lint script itself)
- Uses `subprocess.run()` with `uv run` — requires `uv` to be available in PATH
- Compatible with pytest 7.x+ (uses `Path` parameter type hints on fixtures)

## Security considerations

- Tests use temporary files only — no modification to production databases or source code
- No credentials or secrets used in test data
- Synthetic SQL strings are not valid against any real database

## Rollback considerations

- If tests fail after deployment, verify `rg` is installed and accessible from the test environment
- If `uv` is not available in CI, replace `["uv", "run", "python"]` with `["python"]` and ensure dependencies are installed separately

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| `tests/test_chunks_fts_invariant_lint.py` | Unit: all tests pass | `uv run pytest tests/test_chunks_fts_invariant_lint.py -v` | All tests pass |
| Full test suite | Regression: existing tests still pass | `uv run pytest` | All existing tests pass |

## Completion criteria

- [ ] `tests/test_chunks_fts_invariant_lint.py` exists
- [ ] `test_violation_detected` passes — confirms violation detection works
- [ ] `test_zero_findings_on_sanctioned_path` passes — confirms no false positives on sanctioned path
- [ ] `test_zero_findings_on_mdq_files` passes — confirms no false positives on MDQ files
- [ ] Full test suite passes after adding these tests

## Out of scope

- Testing the tox integration (covered by separate AC-05)
- Testing ADR-009 documentation updates (separate implementation procedures)
- Testing DESIGN-2 status update (separate implementation procedure)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260924-153717 | 20260924-153957 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260924-154004 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260924-154004 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Requirement ID**: REQ-06
- **Source issue**: issues/20260924-054344_design2_no-test-guarantee-chunks_fts-direct-operation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-063321_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121326
- **Related target files**: tests/test_chunks_fts_invariant_lint.py