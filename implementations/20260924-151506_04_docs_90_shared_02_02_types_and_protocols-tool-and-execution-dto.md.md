## Goal
Move `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` to `docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` via `git mv`, with no filename or content change, per Plan `plans/20260924-150508_plan.md` REQ-001.

## Scope
- In scope: the single `git mv` of this file into the new `docs/40_shared/` subfolder.
- Out of scope: any content edit to this file; updating the test file that hardcodes its post-move path (`tests/tools/test_check_docs_quality.py`, handled by seq 15, since this document may modify only one file).

## Assumptions
- `docs/40_shared/` is created once for the whole batch (by seq 01's execution) before this row's `git mv` runs.
- `git mv` preserves `git log --follow` history continuity for a same-content rename.

## Design decisions
A plain `git mv` is used since only the directory location changes.

## Alternatives considered
N/A: a directory move has exactly one correct implementation (`git mv`) for this row.

## Implementation
### Target file
`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`

### Procedure
1. Confirm `docs/40_shared/` exists.
2. Run `git mv docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`.
3. Confirm the move via `git status --short` and `ls docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`.

### Method
`git mv <source> <destination>` — a single Git-tracked rename.

### Details
- Source: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` (confirmed present, 6842 bytes, per Plan Implementation Target Files evidence).
- Destination: `docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`.
- This file is `tests/tools/test_check_docs_quality.py`'s `_KNOWN_DEFECT_PATH` target — that test-fixture path constant fix is a separate row (seq 15), not this document's own responsibility.
- No Front Matter or body edit in this row.

## Compatibility considerations
Bare-filename references continue to resolve via `tools/check_docs_structure.py`'s basename-index resolution. `tests/tools/test_check_docs_quality.py`'s hardcoded flat-path `_KNOWN_DEFECT_PATH` constant will silently start skipping `test_true_positive_known_defect_case` once this move lands, until seq 15's fix runs — expected and covered by REQ-003 (see Plan `plans/20260924-150508_plan.md`).

## Security considerations
N/A: a documentation file rename has no security surface.

## Rollback considerations
Revert via `git mv docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` if needed before commit; after commit, `git revert` the commit that performed this move.

## Validation plan
- `git log --follow docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` shows continuous history through the move (AC-1).
- `ls docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` reports not found; `ls docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` reports found.

## Completion criteria
`docs/40_shared/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` exists with identical content to the pre-move file, the old path no longer exists, and the move is recorded as a Git rename.

## Out of scope
`tests/tools/test_check_docs_quality.py`'s `_KNOWN_DEFECT_PATH` fix (handled by seq 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no test code applies to a pure rename; `_KNOWN_DEFECT_PATH` fix is seq 15 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this row's own file move IS the documentation change |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260923-141137_docsreorg09_move-general-shared-docs-into-new-shared-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-150508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-151506
- **Related target files**: docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md
