## Goal
Add `--dry-run` to `tools/set_execution_status.py` and write its output atomically through the shared helper, with the same exit code as the real run (`REQ-004`, and the related requirements; Plan phase 3).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the write in `update_document`, the `--dry-run` option, and the import block; the companion test.
- Out of scope: rewrite rules and every other option.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `update_document(path, ...)` reads the file with `path.read_text()` (no encoding), rebuilds the Execution Status rows, and writes `"\n".join(rebuilt) + "\n"` with `path.write_text(...)` without an encoding and returns the report lines; `main(argv)` exists and the tool has no `--dry-run`.  The tool is used by path from skills (`uv run python tools/set_execution_status.py`).
- Companion test: `tests/tools/test_set_execution_status.py` (existing file, add a test); it is a valid companion because only this row names it in `Related Tests`.
- The tool has no `sys.path` bootstrap, so it gains the guarded bootstrap to import `tools._atomic_write` when run by path. The helper is `tools/_atomic_write.py` (created by the earlier-`seq` sibling procedure of this Plan). No other open Plan targets this file.

## Design decisions
- The real and dry paths share the same computation and differ only at the write call, so the exit codes cannot diverge (Plan Risks).
- Dry run calls `print_dry_run(path, old_text, new_text)`; the real run calls `atomic_write_text`.

## Alternatives considered
N/A: pattern fixed by the Plan.

## Implementation
### Target file
`tools/set_execution_status.py`

### Procedure
1. Add the guarded bootstrap `if __package__ in (None, ""): sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` (verify `sys` and `Path` are imported) and `from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run` to the imports.
2. Call `add_dry_run_argument(parser)` in the parser setup and pass the flag into `update_document` (a `dry_run` parameter).
3. In `update_document` build the final text, then `print_dry_run(path, original_text, new_text)` when `dry_run`, otherwise `atomic_write_text(path, new_text)`; still return the report lines.

### Method
- Explicit UTF-8 comes from the helper (`REQ-006`); the read stays as it is.
- `find_table` and `apply_updates` stay unchanged (radon grade C 12 each must not rise).

### Details
- Keep the printed report lines identical for the real run; a dry run prints the diff after them.

### Companion test files
- `tests/tools/test_set_execution_status.py`
  - Procedure: add a dry-run test that copies a procedure fixture, runs `main([... , "--dry-run"])`, asserts the sha256 of the file is unchanged, the exit code equals the real run's, and the diff is printed; add a test that the real run writes UTF-8 bytes for a non-ASCII note.
  - Validation: `uv run pytest tests/tools/test_set_execution_status.py -q`.

## Compatibility considerations
- Default behavior, output, and exit codes without `--dry-run` are unchanged; `--dry-run` is new and additive.

## Security considerations
N/A: local files only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_set_execution_status.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: run `uv run python tools/set_execution_status.py` against a temporary copy of a real procedure document with and without `--dry-run`, comparing the report and the resulting file.
- `routing.md` "Adding a new tool" steps 1-3 for the changed files, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- `--dry-run` writes no file (checksum test) and returns the real run's exit code; the real run writes through the helper with explicit UTF-8; no `Path.write_text` call remains in `tools/set_execution_status.py`; tests pass.

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
- **Requirement ID**: `REQ-004`, `REQ-006`, `REQ-007`
- **Source issue**: issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110212_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092109
- **Related target files**: `tools/set_execution_status.py`, `tests/tools/test_set_execution_status.py`
