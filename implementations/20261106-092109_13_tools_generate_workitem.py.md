## Goal
Add `--dry-run` to `tools/generate_workitem.py` and write its output atomically through the shared helper, with the same exit code as the real run (`REQ-004`, and the related requirements; Plan phase 3).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the write in `main`, the `--dry-run` option, and the import block; the companion test.
- Out of scope: rewrite rules and every other option.

## Assumptions
- Verified on 2026-11-06 (Step 3a): three writes exist: `find_or_record_pass_timestamp` rewrites the plan file with a timestamp marker appended, `generate_all_rows` writes each skeleton after `check_collision` (printing `SKIP (exists)` for a collision) and `main` writes the single skeleton and prints `Created <path>`; `main(argv)` exists and has no `--dry-run`. The collision refusal stays before every write; the helper's replace would overwrite a file created between the check and the write, which is the same window as today. The plan-marker write is the only place that rewrites an existing document.
- Companion test: `tests/tools/test_generate_workitem.py` (existing file, add a test); it is a valid companion because only this row names it in `Related Tests`.
- The tool has no `sys.path` bootstrap, so it gains the guarded bootstrap to import `tools._atomic_write` when run by path. The helper is `tools/_atomic_write.py` (created by the earlier-`seq` sibling procedure of this Plan). No other open Plan targets this file.

## Design decisions
- The real and dry paths share the same computation and differ only at the write call, so the exit codes cannot diverge (Plan Risks).
- Dry run calls `print_dry_run(path, old_text, new_text)`; the real run calls `atomic_write_text`.

## Alternatives considered
N/A: pattern fixed by the Plan.

## Implementation
### Target file
`tools/generate_workitem.py`

### Procedure
1. Add the guarded bootstrap `if __package__ in (None, ""): sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` (verify `sys` and `Path` are imported) and `from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run` to the imports.
2. Call `add_dry_run_argument(parser)`; thread `dry_run` into `find_or_record_pass_timestamp`, `generate_all_rows`, and the single-skeleton path.
3. Replace the three `write_text` calls with `atomic_write_text` (real run) or `print_dry_run` (dry run; a new file prints a diff against empty and the `Created` line reads `Would create`); the marker line is computed in both modes but not persisted in a dry run.

### Method
- The shared timestamp for one pass stays correct in a dry run because the computed value is returned even when the marker is not written.

### Details
- A dry run must not create or modify any file, including the plan marker; verify with a checksum of the plan and a directory listing.

### Companion test files
- `tests/tools/test_generate_workitem.py`
  - Procedure: add a dry-run test: after `main([... , "--dry-run"])` the output directory listing and the plan checksum are unchanged, the exit code equals the real run's, and the printed diff mentions the skeleton path; the existing tests keep passing.
  - Validation: `uv run pytest tests/tools/test_generate_workitem.py -q`.

## Compatibility considerations
- Default behavior, output, and exit codes without `--dry-run` are unchanged; `--dry-run` is new and additive.

## Security considerations
N/A: local files only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_generate_workitem.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: run the tool with `--dry-run` for a real plan and row and compare the printed names with a real run in a temporary copy of the repository layout.
- `routing.md` "Adding a new tool" steps 1-3 for the changed files, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- `--dry-run` writes no file (checksum test) and returns the real run's exit code; the real run writes through the helper with explicit UTF-8; no `Path.write_text` call remains in `tools/generate_workitem.py`; tests pass.

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
- **Related target files**: `tools/generate_workitem.py`, `tests/tools/test_generate_workitem.py`
