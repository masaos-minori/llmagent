## Goal
- Add unit tests for sibling resolution in `tests/tools/test_stale_detector.py` (`REQ-001`: resolved name and report, `REQ-002`: order rule and options, `REQ-003`: unchanged and edge cases).

## Scope
- Modify only `tests/tools/test_stale_detector.py`; append new test classes. Blast radius Low. The behavior under test is built by procedure `01` (`seq` 01).

## Assumptions
- A1: Step 3a: the module has classes such as `TestFromProcedureDeclaredNewTarget` that build procedures in `tmp_path` and call `StaleResult.from_procedure(proc, source_dir)`; the same fixture style is reused (verified by Read, 2026-11-02).
- A2: The names `sibling_mode` (new), `resolved`, `warnings`, and the options `--sibling-order` and `--no-siblings` are created by the `seq` 01 procedure (declared `(new)` in its Design decisions and Procedure), so they exist when this document runs. They are mentioned here as plain words, not backticked source symbols, except where noted.
- A3: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): `tests/tools/test_stale_detector.py` is also targeted by `plans/20261102-080828_flowimp009_test-row-grouping.md`. Judged a sequencing dependency, not a conflict: this Plan adds a sibling pass after the per-document checks, that Plan changes how the document's own target and companions are read first; whichever lands second rebases (Plan A8). Locate code by symbol name, not line number.

## Design decisions
- One new class per behavior group; fixtures create `implementations/` and `implementations/done/` inside `tmp_path`, with file names `20261102-000000_01_a.md`, `_02_b.md`, and Traceability `Source plan` lines.
- Assert on result fields and on `summary` text, and run `main` once for the CLI options.

## Alternatives considered
- N/A: placement and style fixed by the existing module.

## Implementation
### Target file
`tests/tools/test_stale_detector.py`

### Procedure
1. Add a helper `_write_procedure` (new) that writes a minimal procedure with a Target file section, body text, and a Traceability block with a chosen `Source plan`.
2. Add `TestSiblingResolution` (new) and `TestSiblingOrderRule` (new) and `TestSiblingEdgeCases` (new).
3. Run the whole module plus `tests/tools/test_mark_procedure_new_symbols.py` unchanged.

### Method
- Resolution: sibling A (seq 01) marks a name `(new)`; document B (seq 02) cites it unmarked; B is not stale, `resolved` names A, the summary has the informational line; a name marked nowhere is still reported.
- Order: name declared only by a later sibling stays stale with the reason text; with the accept-any mode it resolves; the printed rule line is `earlier` or `any`; disabled mode reports the name stale and prints no sibling lines.
- Edge cases: no `Source plan` (output equal to the run with siblings disabled); `Source plan` of `N/A`; no siblings; unreadable sibling (invalid UTF-8 bytes) gives a warning and a clean result for a resolvable document; declaration cycle resolves only for the later document; a sibling in `implementations/done/` counts; an import marked `(new)` in a sibling resolves an `import_missing`; the document itself is not its own sibling; a `plans/` versus `plans/done/` path in `Source plan` matches by basename.
- CLI: `main([...,"--no-siblings"])` and `main([...,"--sibling-order","any"])` exit codes and output.

### Details
- Use real marker text `` `name` (new) `` in fixtures; fixture symbol names use CamelCase so they pass the minimum-shape heuristic.
- Do not modify existing tests.

## Compatibility considerations
- N/A: tests only; no existing test is edited.

## Security considerations
- N/A: tests use `tmp_path` only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_stale_detector.py tests/tools/test_mark_procedure_new_symbols.py -v`: all pass.
- `uv run ruff format tests/tools/test_stale_detector.py` and `uv run ruff check tests/tools/test_stale_detector.py`: clean.

## Completion criteria
- Every case in the Plan Tests section for `REQ-001` to `REQ-003` has a test (resolved, unresolved, later-only, accept-any, disable, no `Source plan`, no siblings, unreadable sibling, cycle, archived sibling); the existing suites pass unchanged.

## Out of Scope
- Companion-file tests (flowimp009 Plan); changes to existing tests; the baseline measurement over archived procedures (a check step of the Plan, not a file change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the sibling test classes and helper to `tests/tools/test_stale_detector.py` | Completed | 20261102-130942 | 20261102-130942 | Files: tests/tools/test_stale_detector.py (+20 tests, main import added). Step 2 clean; Step 3a: A1 verified, no correction. |
| 2 | Run the module and the consumer suite `tests/tools/test_mark_procedure_new_symbols.py` unchanged | Completed | 20261102-130942 | 20261102-130942 | 131 passed (stale_detector + mark_procedure_new_symbols). testmon-forceselect: 119 passed, 1 known pre-existing failure. Full suite deferred to plan end. |
| 3 | Run ruff format and check on the test file (`rules/toolchain.md`) | Completed | 20261102-130942 | 20261102-130942 | ruff format/check, mypy on test file clean. No docs row (N/A). |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20261030-191457_flowimp007_stale-sibling-new.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080513_flowimp007_stale-sibling-new.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085029
- **Related target files**: `tests/tools/test_stale_detector.py`