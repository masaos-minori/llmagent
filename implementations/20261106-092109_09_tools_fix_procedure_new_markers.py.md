## Goal
Add `--dry-run` to `tools/fix_procedure_new_markers.py` and write its output atomically through the shared helper, with the same exit code as the real run (`REQ-004`, and the related requirements; Plan phase 3).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the write in `main`, the `--dry-run` option, and the import block; the companion test.
- Out of scope: rewrite rules and every other option.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `main(argv)` loops over the given files, computes `new_text, count = add_markers(text, symbols)`, calls `file_path.write_text(new_text, encoding="utf-8")` when `count` is non-zero, prints `<file>: N marker(s) added` and `total: N`, and returns `1` for a path that is not a file; the tool has no `--dry-run`.  No test references the tool today (checked with `rg`).
- Companion test: `tests/tools/test_fix_procedure_new_markers.py` (new file, no test exists today); it is a valid companion because only this row names it in `Related Tests`.
- The tool has no `sys.path` bootstrap, so it gains the guarded bootstrap to import `tools._atomic_write` when run by path. The helper is `tools/_atomic_write.py` (created by the earlier-`seq` sibling procedure of this Plan). No other open Plan targets this file.

## Design decisions
- The real and dry paths share the same computation and differ only at the write call, so the exit codes cannot diverge (Plan Risks).
- Dry run calls `print_dry_run(path, old_text, new_text)`; the real run calls `atomic_write_text`.

## Alternatives considered
N/A: pattern fixed by the Plan.

## Implementation
### Target file
`tools/fix_procedure_new_markers.py`

### Procedure
1. Add the guarded bootstrap `if __package__ in (None, ""): sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` (verify `sys` and `Path` are imported) and `from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run` to the imports.
2. Call `add_dry_run_argument(parser)` and read `args.dry_run`.
3. Replace the `write_text` call with `print_dry_run(file_path, text, new_text)` under `--dry-run` and `atomic_write_text(file_path, new_text)` otherwise; the marker count and prints stay identical.

### Method
- `add_markers` is untouched; the `ERROR: not a file` path and its exit code `1` are unchanged.

### Details
- In a dry run the `<file>: N marker(s) added` lines are still printed (the count is what would be added) so output stays comparable.

### Companion test files
- `tests/tools/test_fix_procedure_new_markers.py` (new)
  - Procedure: add a new test file: `--dry-run` leaves the file byte-identical and returns the real run's exit code, the real run adds the markers atomically with UTF-8, and a missing file returns `1` in both modes.
  - Validation: `uv run pytest tests/tools/test_fix_procedure_new_markers.py -q`.

## Compatibility considerations
- Default behavior, output, and exit codes without `--dry-run` are unchanged; `--dry-run` is new and additive.

## Security considerations
N/A: local files only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_fix_procedure_new_markers.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: run the tool with and without `--dry-run` on a temporary copy of a procedure document.
- `routing.md` "Adding a new tool" steps 1-3 for the changed files, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- `--dry-run` writes no file (checksum test) and returns the real run's exit code; the real run writes through the helper with explicit UTF-8; no `Path.write_text` call remains in `tools/fix_procedure_new_markers.py`; tests pass.

## Out of Scope
- Rewrite rules, other tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the dry-run test first (fails until step 2) per Companion test files | Pending | — | — | |
| 2 | Add `--dry-run` and the helper write per Implementation > Procedure | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the live-data comparison | Pending | — | — | |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`, `REQ-005`, `REQ-007`
- **Source issue**: issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110212_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092109
- **Related target files**: `tools/fix_procedure_new_markers.py`, `tests/tools/test_fix_procedure_new_markers.py`
