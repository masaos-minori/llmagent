## Goal

Add guard tests for config_loader.py before refactoring to establish behavioral baseline for file merge order, restrict_to isolation, and extension resolution.

## Scope

**In-Scope:**
- Create `tests/shared/test_config_loader.py` with tests for:
  - File merge order: later files override earlier ones
  - restrict_to isolation: calling restrict_to() doesn't leak state between tests
  - Extension resolution: missing extensions resolved correctly
  - Global state cleanup: class variables properly reset after each test

**Out-of-Scope:**
- Changing the behavior of ConfigLoader itself
- Any changes beyond the test

## Assumptions

1. The loader needs characterization tests since it has strong side effects from class variable-based global state
2. Tests must use pytest fixtures to ensure clean state between tests
3. Tests should verify current behavior, not expected future behavior

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for config loader edge cases | Search for `config_loader` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/shared/test_config_loader.py`

- **Blast Radius:**
  - Test-only change — no production code affected

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `config_loader.py`:
```python
# Class-level state: _allowed_files (set by restrict_to(), persists across instances)
# Key behaviors:
# - load(): merges multiple config files, excludes keys starting with "_"
# - load_all(): loads base config files in dependency order, deep-merges dicts
# - restrict_to(): sets class-level whitelist, affects all subsequent calls
# - _resolve_path(): appends .toml extension if missing
```

The test will verify merge order, restrict_to isolation, extension resolution, and global state cleanup.

## Implementation

### Target file
New file: `tests/shared/test_config_loader.py`

### Procedure
1. Verify `tests/shared/` directory exists
2. Create new test file `tests/shared/test_config_loader.py`
3. Write tests for file merge order
4. Write tests for restrict_to isolation
5. Write tests for extension resolution
6. Write tests for global state cleanup
7. Save the file

### Method
Create characterization tests using pytest fixtures to ensure clean state between tests.

### Details
1. Create `tests/shared/test_config_loader.py`:
   ```python
   """Characterization tests for ConfigLoader."""
   
   import pytest
   from pathlib import Path
   from shared.config_loader import ConfigLoader
   
   @pytest.fixture(autouse=True)
   def reset_class_state():
       """Reset class-level state before each test."""
       ConfigLoader._allowed_files = None
       yield
       ConfigLoader._allowed_files = None
   
   def test_merge_order_later_overrides_earlier(tmp_path):
       """Later files override earlier ones."""
       (tmp_path / "a.toml").write_text("[section]\nfoo = 1\n")
       (tmp_path / "b.toml").write_text("[section]\nbar = 2\n")
       loader = ConfigLoader(config_dir=tmp_path)
       result = loader.load("a.toml", "b.toml")
       assert result["section"]["foo"] == 1
       assert result["section"]["bar"] == 2
   
   def test_restrict_to_isolation(tmp_path):
       """restrict_to() doesn't leak state between tests."""
       ConfigLoader.restrict_to("a.toml")
       loader = ConfigLoader(config_dir=tmp_path)
       with pytest.raises(Exception):  # ConfigPermissionError
           loader.load("b.toml")
       # After this test, _allowed_files should be reset by fixture
   
   def test_extension_resolution(tmp_path):
       """Missing .toml extension is appended automatically."""
       (tmp_path / "test.toml").write_text("[section]\nfoo = 1\n")
       loader = ConfigLoader(config_dir=tmp_path)
       result = loader.load("test")
       assert result["section"]["foo"] == 1
   
   def test_global_state_cleanup(tmp_path):
       """Class variables are properly reset after each test."""
       ConfigLoader.restrict_to("a.toml")
       assert ConfigLoader._allowed_files == frozenset({"a.toml"})
       # Fixture resets _allowed_files to None
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

N/A — this test documents current behavior

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_config_loader.py` | Characterization tests document current behavior | `uv run pytest -k "config_loader" -v` | All tests pass |

## Out of scope

- Changing the behavior of ConfigLoader itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-130126_require.md
- Source plan: plans/20260726-172449_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/shared/config_loader.py, tests/shared/test_config_loader.py
