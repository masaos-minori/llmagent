## Goal
Remove the now-invalid `patch("rag.pipeline._ModuleConfig.get", ...)` wrappers in this
file's `_make_pipeline()` helpers so the suite keeps passing once `_ModuleConfig` is
removed from `scripts/rag/pipeline.py` (REQ-004).

## Scope
- In scope: the two `with patch("rag.pipeline._ModuleConfig.get", return_value={}):`
  blocks (one per test class helper) — dedent the `return RagPipeline(http, cfg)` call
  each wraps and delete the `with` line.
- Out of scope: any other `patch(...)` call in this file (e.g. the unrelated
  `rag.pipeline.SQLiteHelper` patch at line 207); `scripts/rag/pipeline.py` itself
  (tracked in this Plan's seq 01 row).

## Assumptions
- **Correction to the Plan's claim (2026-09-06)**: the Plan's Implementation Target
  Files row and Design section state "3 occurrences" at lines 204, 284, 368. Direct
  read this cycle (`grep -n "patch(\|_ModuleConfig" tests/rag/test_rag_pipeline.py`,
  full file also read, 320 lines) confirms only **2** occurrences of
  `patch("rag.pipeline._ModuleConfig.get", ...)` exist, at lines 201 and 278 — both
  inside a `_make_pipeline()` helper method, one in `TestRagPipelineErrorOnDbOpen`
  (line 201) and one in `TestGetDiagnostics` (line 278). Line 207 is an unrelated
  `patch("rag.pipeline.SQLiteHelper", ...)` call the Plan's citation apparently
  conflated with the `_ModuleConfig` count. This document proceeds against the
  confirmed actual count (2, not 3) and actual line numbers (201, 278, not 204/284/368)
  — the Plan document itself is not edited by this row (per workflow.md Step 3a, a
  fork processing a single row does not edit the shared Plan; this discrepancy is
  reported to the coordinating session instead).
- Confirmed: both helpers construct `cfg` as a `SimpleNamespace` (has `__dict__`), so
  `RagPipeline.__init__`'s object-with-`__dict__` resolution branch is taken at
  runtime, never `_ModuleConfig.get()` — the patch is defensive/inert in both cases,
  matching the Plan's Design-section reasoning (only the count/line-number citation
  was stale, not the underlying behavioral claim).

## Design decisions
- Remove the `with patch("rag.pipeline._ModuleConfig.get", return_value={}):` line and
  dedent the single `return RagPipeline(http, cfg)` statement it wraps, in both
  `_make_pipeline()` helpers — no other change to either helper or its surrounding
  test class.

## Alternatives considered
- Replace the patch with a no-op context manager instead of removing it: rejected —
  the patch target (`rag.pipeline._ModuleConfig`) no longer exists after REQ-002 lands,
  so any reference to it (even a no-op wrapper) is dead weight; plain removal is the
  correct fix per the Plan's own Design section reasoning.

## Implementation
### Target file
`tests/rag/test_rag_pipeline.py`

### Procedure
1. In `TestRagPipelineErrorOnDbOpen._make_pipeline()` (currently lines 169-202):
   remove line 201 (`with patch("rag.pipeline._ModuleConfig.get", return_value={}):`)
   and dedent line 202 (`return RagPipeline(http, cfg)`) by one indent level.
2. In `TestGetDiagnostics._make_pipeline()` (currently lines 246-279): remove line 278
   (`with patch("rag.pipeline._ModuleConfig.get", return_value={}):`) and dedent line
   279 (`return RagPipeline(http, cfg)`) by one indent level.
3. Leave the unrelated `patch("rag.pipeline.SQLiteHelper", ...)` block (line 207) and
   all other test code in this file unchanged.

### Method
Confirmed this cycle (2026-09-06) via direct read of the full file (320 lines) and
`grep -n "patch(\|_ModuleConfig"` — exactly 2 matching patch blocks exist, at lines 201
and 278, each the sole line inside its class's `_make_pipeline()` helper.

### Details
No change to any assertion, fixture data, or test method body — only the two `with`
wrappers and their single-statement bodies' indentation.

## Compatibility considerations
Both helpers build `cfg` as a `SimpleNamespace`, so `RagPipeline.__init__` (and, after
this Plan's seq 01 row lands, `resolve_rag_config`) resolves `cfg` via the
object-with-`__dict__` branch in both cases — removing the `_ModuleConfig.get()` patch
does not change what either test actually exercises or asserts.

## Security considerations
N/A: test-only change, no production code path affected.

## Rollback considerations
Revert via `git checkout` on this file alone if `uv run pytest
tests/rag/test_rag_pipeline.py -v` fails after the edit.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py -v` — all tests pass, no
  `AttributeError` from patching a removed `_ModuleConfig` class.
- `uv run pytest -v` (full suite) — no new failures, per this Plan's Tests section.

## Completion criteria
- Both `_make_pipeline()` helpers construct and return `RagPipeline(http, cfg)` with no
  `patch("rag.pipeline._ModuleConfig...")` wrapper remaining anywhere in this file.
- `uv run pytest tests/rag/test_rag_pipeline.py -v` passes after
  `scripts/rag/pipeline.py`'s `_ModuleConfig` removal (this Plan's seq 01 row) lands.

## Out of scope
- `scripts/rag/pipeline.py` — tracked in seq 01.
- The unrelated `rag.pipeline.SQLiteHelper` patch in this same file (line 207) — not
  part of REQ-004's scope.

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260905-192946_refactor_ragpipeline_responsibility_boundaries.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260906-115512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-152050
- **Related target files**: tests/rag/test_rag_pipeline.py
