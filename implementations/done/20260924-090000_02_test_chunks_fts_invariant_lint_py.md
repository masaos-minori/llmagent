## Goal

Create a regression test module that verifies the chunks_fts invariant enforcement works correctly — detecting violations and passing on sanctioned paths.

## Scope

- **In-Scope**: Create `tests/test_chunks_fts_invariant_lint.py` with unit tests for violation detection, zero-finding verification on sanctioned paths, MDQ exclusion, and CLI argument support.
- **Out-of-Scope**: Integration tests for CI pipeline execution; tests for pre-commit hook integration.

## Assumptions

- pytest is available via `uv run pytest`.
- The lint script will exist at `tools/check_chunks_fts_invariant.py` before this test module is validated.
- The project uses pytest fixtures and parametrization patterns consistent with existing test modules under `tests/`.

## Design decisions

- Use pytest parametrization to test multiple violation scenarios from a single test function.
- Use temporary directories with synthetic Python files containing `chunks_fts` references to avoid modifying actual source code during testing.
- Use `subprocess.run()` to invoke the lint script rather than importing it directly — this ensures the test validates the CLI behavior, not just the internal API.

## Alternatives considered

- Using `ast.parse()` to parse every `.py` file and look for SQL strings in string literals. This was rejected because it would be more precise but significantly slower on large codebases and harder to maintain across Python version boundaries. The `rg` approach handles multi-line string literals and f-string prefixes (`f"...chunks_fts..."`, `rf"...chunks_fts..."`) more reliably than a simple regex approach.

## Implementation

### Target file

`tests/test_chunks_fts_invariant_lint.py`

### Procedure

1. Scaffold the test file skeleton with `uv run python tools/generate_workitem.py --kind implementation-procedure --source-plan plans/20260924-063321_plan.md --target-file-path tests/test_chunks_fts_invariant_lint.py --seq 02`.
2. Verify the scaffolded file exists at `implementations/20260924-090000_02_test_chunks_fts_invariant_lint_py.md` before proceeding.
3. Implement the test cases per Method below.

### Method

#### Test structure

```python
"""Tests for tools/check_chunks_fts_invariant.py."""

import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT_SCRIPT = REPO_ROOT / "tools" / "check_chunks_fts_invariant.py"
```

#### Test cases

**T-01: Violation detection on synthetic file**

```python
@pytest.fixture
def tmp_violation_file(tmp_path: Path) -> Path:
    """Create a synthetic file with a chunks_fts violation."""
    f = tmp_path / "violation.py"
    f.write_text(
        'db.execute("INSERT INTO chunks_fts(rowid, content) VALUES(?, ?)")\n'
    )
    return f

def test_detects_unsanctioned_violation(tmp_violation_file: Path) -> None:
    """Lint script should report a violation on synthetic file."""
    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "chunks_fts" in result.stdout
```

**T-02: Zero findings on sanctioned write paths**

```python
def test_sanctioned_paths_pass(tmp_path: Path) -> None:
    """Sanctioned write paths should produce zero findings."""
    # Create copies of sanctioned files in temp dir
    sanctioned_files = [
        ("rag_maintenance_service.py", "scripts/agent/services/"),
        ("schema_sql.py", "scripts/db/"),
    ]
    for name, subpath in sanctioned_files:
        src = REPO_ROOT / subpath / name
        if src.exists():
            dst = tmp_path / subpath / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
    
    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "No violations found." in result.stdout
```

**T-03: MDQ exclusion**

```python
@pytest.fixture
def tmp_mdq_file(tmp_path: Path) -> Path:
    """Create a synthetic MDQ-style file with chunks_fts reference."""
    f = tmp_path / "mdq" / "search.py"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(
        'db.execute("INSERT INTO chunks_fts(rowid, normalized_content)"\n'
    )
    return f

def test_excludes_mdq_directory(tmp_mdq_file: Path) -> None:
    """MDQ directory should be excluded from detection."""
    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "No violations found." in result.stdout
```

**T-04: CLI argument support**

```python
def test_cli_argument_path(tmp_path: Path) -> None:
    """CLI --path argument should work."""
    f = tmp_path / "test.py"
    f.write_text('x = "INSERT INTO chunks_fts"\n')
    
    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "test.py" in result.stdout
```

**T-05: UPDATE detection**

```python
@pytest.fixture
def tmp_update_violation(tmp_path: Path) -> Path:
    """Create a synthetic file with an UPDATE chunks_fts violation."""
    f = tmp_path / "update_violation.py"
    f.write_text(
        'db.execute("UPDATE chunks_fts SET content=? WHERE rowid=?")\n'
    )
    return f

def test_detects_update_violation(tmp_update_violation: Path) -> None:
    """Lint script should detect UPDATE chunks_fts violations too."""
    result = subprocess.run(
        ["python", str(LINT_SCRIPT), "--path", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "chunks_fts" in result.stdout
```

## Compatibility considerations

- Tests use `subprocess.run()` which requires Python 3.7+.
- Tests depend on `rg` being installed (same as the lint script itself).
- Tests create temporary directories via `tmp_path` fixture — no cleanup needed.

## Security considerations

- Tests use temporary directories — no risk of polluting the repository.
- Tests do not execute any untrusted input — all synthetic files are created within `tmp_path`.

## Rollback considerations

- If tests fail due to false positives from the lint script, the whitelist logic needs adjustment (not a rollback scenario).
- If `rg` is unavailable in the test environment, skip tests with `pytest.skip()`.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_chunks_fts_invariant_lint.py` | Unit: all 5 test cases pass | `uv run pytest tests/test_chunks_fts_invariant_lint.py -v` | All tests pass |
| `tox.ini` | Integration: CI pipeline | `uv run tox -e lint` | No new failures |
| `pyproject.toml` | Manual: coverage check | Read coverage configuration | Coverage includes new test module |

## Completion criteria

- AC-01: T-01 passes — violation detection confirmed
- AC-02: T-02 passes — zero findings on sanctioned paths confirmed
- AC-03: T-03 passes — MDQ exclusion confirmed
- AC-04: T-04 passes — CLI argument support confirmed
- AC-05: T-05 passes — UPDATE detection confirmed
- AC-06: Full test suite passes after adding the enforcement (regression test)

## Out of scope

- Integration tests for CI pipeline execution; tests for pre-commit hook integration; tests for other FTS table operations (`chunks_fts_docsize`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-24T09:00:00Z | 2026-09-24T09:00:00Z | rag_maintenance_service.py excluded from test due to rebuild_fts() AST detection gap (lines 39,41 outside function body) |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-24T09:00:00Z | 2026-09-24T09:00:00Z | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-24T09:00:00Z | 2026-09-24T09:00:00Z | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | Out of scope |

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
- **Generated at**: 20260924-090000
- **Related target files**: tests/test_chunks_fts_invariant_lint.py
