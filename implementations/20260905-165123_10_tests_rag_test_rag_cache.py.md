## Goal
Delete `tests/rag/test_rag_cache.py` in its entirety — it tests `SemanticCache`
directly (zero/negative capacity, FIFO pruning, invalidation, history-context
separation, dimension mismatch, lock re-entrancy), a class this Plan removes
(`REQ-006`).

## Scope
- **In-Scope**: delete the file `tests/rag/test_rag_cache.py` (103 lines).
- **Out-of-Scope**: every other test file in `tests/rag/` — confirmed unaffected by
  its own filename/content, not this file's.

## Assumptions
- `scripts/rag/cache.py` (procedure document `02`) is deleted in the same
  implementation pass — this test file's sole subject under test no longer exists once
  that document lands.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Delete the whole file rather than gutting individual test functions — its own module
  docstring confirms every test in it targets `SemanticCache` behavior with no
  unrelated content to preserve.

## Alternatives considered
N/A: whole-file deletion is the only option once the class under test is removed —
partial retention would leave untestable stubs.

## Implementation
### Target file
`tests/rag/test_rag_cache.py`

### Procedure
1. Delete the file `tests/rag/test_rag_cache.py`.

### Method
File deletion.

### Details
- Confirm `scripts/rag/cache.py` (procedure `02`) is deleted in the same pass, so no
  `pytest` collection attempts to import this test file against a module that no
  longer exists (which would otherwise surface as a collection error rather than a
  clean absence).

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A.

## Rollback considerations
- Revert via restoring the deleted file from version control; must be reverted
  together with procedure document `02` (`scripts/rag/cache.py`) since this test
  imports from that module.

## Validation plan
- `uv run pytest tests/rag/ -v` — no collection error from a missing test file (its
  absence is expected); full `tests/rag/` suite passes.

## Completion criteria
- `tests/rag/test_rag_cache.py` no longer exists (Plan `AC-6`, `AC-9`).

## Out of scope
- `scripts/rag/cache.py` itself (procedure document `02`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: deletion only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-006` (delete `tests/rag/test_rag_cache.py`)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/rag/test_rag_cache.py
