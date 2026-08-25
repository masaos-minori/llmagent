# Implementation Procedure: Fix rename_modules.py hardcoded path and silent-failure behavior

## Goal

Make `rename_modules.py` work correctly across environments by deriving the repository root from the script's own location instead of a hardcoded absolute path, and fail loudly (non-zero exit + clear error message) when required paths do not exist.

## Scope

- **In-Scope**: `tools/rename_modules.py` (module-level `BASE`, `main()`)
- **Out-of-Scope**: Any actual module rename operation against `scripts/mcp_servers/`, rewriting the import/docstring/patch-target update logic beyond fixing the described base-path and dead-code issues, any other `tools/*.py` script.

## Assumptions

- Deriving `BASE` from `Path(__file__).resolve().parent.parent` is acceptable — this assumes the script is always invoked as `python tools/rename_modules.py` from within the repository, not installed as a package entry point.
- The existing `continue`-based skip inside the loop is intentional for optional directories (e.g., `mutants/` may not exist in all environments). Only `BASE` itself should fail loudly; individual subdirectories can remain optional.
- The separately-reported dead-code duplication between `process_file()` and `main()` is out of scope unless trivial to fix alongside the base-path change.

## Design decisions

### Derive BASE from script location

Replace `BASE = pathlib.Path("/home/sugimoto/llmagent")` with:
```python
BASE = pathlib.Path(__file__).resolve().parent.parent
```
This matches the pattern used by `tools/manage_frontmatter.py` (line 25: `ROOT_DIR = Path(__file__).resolve().parent.parent`), `tools/check_no_compat.py`, and `tools/gen_reference_table.py`.

### Fail-loud for missing BASE only

Add an existence check on `BASE` at the start of `main()` that exits non-zero with a clear error if the path is missing. Do NOT add similar checks for individual subdirectories (`scripts/`, `tests/`, `mutants/`, etc.) — these are optional and may not exist in all environments. The existing `continue`-based skip remains for those.

### Keep process_file() for now

The issue mentions dead-code duplication between `process_file()` and `main()`. Leave this out of scope unless trivially fixable alongside the base-path change. Investigate during implementation.

## Alternatives considered

- **Use `sys.argv[0]` to derive the repo root**. Rejected because it fails when the script is invoked via `python -c` or as a package entry point.
- **Accept `--repo-root` CLI argument**. Rejected because it adds complexity and doesn't solve the default case where users expect the script to work without arguments.

## Implementation

### Target file

`tools/rename_modules.py`

### Procedure

#### Phase 1: Fix BASE resolution

Replace `BASE = pathlib.Path("/home/sugimoto/llmagent")` with `BASE = pathlib.Path(__file__).resolve().parent.parent`

#### Phase 2: Add fail-loud check for missing BASE

At the start of `main()`, add:
```python
if not BASE.is_dir():
    print(f"ERROR: repository root not found: {BASE}", file=sys.stderr)
    sys.exit(1)
```

#### Phase 3: Investigate process_file() dead-code concern

Search for call sites of `process_file()` to determine if it's unused. If trivial, route `main()` through `process_file()` for consistency. Out of scope if non-trivial.

#### Phase 4: Update documentation

Review and update the script's docstring/usage notes if they reference a specific path.

#### Phase 5: Add tests

1. Create `tests/tools/test_rename_modules.py` with temp directory fixture
2. Test: correct root resolution independent of running user's home directory
3. Test: non-zero exit with clear error when target directory is absent

#### Phase 6: Validation

1. Run `uv run pytest tests/tools/test_rename_modules.py -v`
2. Run `uv run ruff check tools/rename_modules.py`
3. Run `uv run mypy tools/rename_modules.py`

### Method

Phase 1 changes the module-level constant at line 8:
```python
# Before:
BASE = pathlib.Path("/home/sugimoto/llmagent")

# After:
BASE = pathlib.Path(__file__).resolve().parent.parent
```

Phase 2 adds a guard at the start of `main()` (before line 421):
```python
def main() -> None:
    if not BASE.is_dir():
        print(f"ERROR: repository root not found: {BASE}", file=sys.stderr)
        sys.exit(1)
    
    dirs_to_process = [
        BASE / "scripts",
        ...
    ]
```

Phase 3 requires investigation. Verified against current source: `process_file()` is defined at line 383 but never called within the same file. The `main()` function has its own inline logic (lines 440-467) that duplicates what `process_file()` does. This confirms the dead-code concern raised in the issue.

### Details

Verified against current source:
- Line 8: `BASE = pathlib.Path("/home/sugimoto/llmagent")` — confirmed, hardcoded absolute path
- Lines 421-428: `main()` builds `dirs_to_process` using `BASE / "scripts"`, etc. — confirmed
- Line 434: `if not d.exists(): continue` — confirmed, silently skips missing directories
- Line 469: Prints "Done. Updated 0/0 files." even when all directories were skipped — confirmed
- `process_file()` at line 383: never called within the same file — confirmed dead code

## Compatibility considerations

- Retaining `continue`-based skip for individual subdirectories ensures backward compatibility with environments where some directories don't exist
- Adding a fail-loud check for `BASE` is a behavioral breaking change for users relying on the current silent-no-op behavior
- Document the change clearly in the Usage docstring

## Security considerations

N/A: no security-sensitive operations affected.

## Rollback considerations

If the fail-loud check breaks workflows, revert by removing the new check. The rollback is a single-block removal.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/rename_modules.py` | Unit test — root resolution | `uv run pytest tests/tools/test_rename_modules.py::test_root_resolution -v` | Exit 0, BASE resolved correctly |
| `tools/rename_modules.py` | Unit test — missing path | `uv run pytest tests/tools/test_rename_modules.py::test_missing_path_exits_nonzero -v` | Non-zero exit, error message names missing path |
| `tools/rename_modules.py` | Lint | `uv run ruff check tools/rename_modules.py` | Clean (no errors) |
| `tools/rename_modules.py` | Type check | `uv run mypy tools/rename_modules.py` | Clean (no new regressions) |

## Completion criteria

- [ ] Script resolves BASE correctly from any path
- [ ] Non-zero exit with explicit error when path is missing
- [ ] Regression test covers both assertions

## Out of scope

- Removing `process_file()` entirely (dead-code cleanup)
- Changing the `continue`-based skip for optional subdirectories
- Adding a separate `--repo-root` CLI flag
- Modifying any other `tools/*.py` script

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 through REQ-003
- **Source issue**: issues/20260824_02_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-175012_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-180023
- **Related target files**: tools/rename_modules.py
