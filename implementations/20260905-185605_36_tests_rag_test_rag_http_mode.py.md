## Goal
Remove `cfg.use_semantic_cache = False` from `tests/rag/test_rag_http_mode.py`'s
`_make_pipeline()` fixture, made obsolete by procedure document `03` (`RAGConfig`'s
field removal) (`REQ-009`).

## Scope
- **In-Scope**: remove `cfg.use_semantic_cache = False` (line 24) from
  `_make_pipeline()`.
- **Out-of-Scope**: every other line in `_make_pipeline()` — confirmed unrelated;
  `pipeline.semantic_cache = MagicMock()` (line 32, same function) — owned by
  `semcacherm`'s own procedure document `18`
  (`implementations/20260905-165123_18_tests_rag_test_rag_http_mode.py.md`) — see
  Assumptions for the same cross-Plan overlap pattern as procedure document `33`.

## Assumptions
- Same cross-Plan overlap as procedure document `33`
  (`tests/rag/test_pipeline_http_result_kind.py`): this exact line is named in both
  this Plan and the `semcacherm` Plan's procedure document `18`, converging on the
  same removal — whichever lands first makes the other's corresponding step a no-op.
- `cfg` is a `MagicMock()` in this fixture, same as procedure document `33`'s file —
  this document's change is safe to apply independently of `RAGConfig`'s/
  `RagConfigImpl`'s field-removal landing order.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Scope this document to exactly the one line this Plan's own Requirement (`REQ-009`)
  covers, leaving `pipeline.semantic_cache = MagicMock()` to `semcacherm`'s own
  procedure document `18` — same reasoning as procedure document `33`.

## Alternatives considered
- Removing both lines in this document — rejected, same reasoning as procedure
  document `33`.

## Implementation
### Target file
`tests/rag/test_rag_http_mode.py`

### Procedure
1. Check whether `cfg.use_semantic_cache = False` (originally line 24) is still
   present before editing — if `semcacherm`'s procedure document `18` has already
   removed it, this step is a no-op: confirm via `rg -n "cfg.use_semantic_cache"
   tests/rag/test_rag_http_mode.py` returning zero matches, and record this row as
   `Already implemented` rather than re-editing.
2. If still present, remove `cfg.use_semantic_cache = False`.

### Method
Direct removal via `Edit`, conditional on presence (see Procedure step 1).

### Details
- Do not remove `pipeline.semantic_cache = MagicMock()` here — owned by
  `semcacherm`'s own procedure document `18`.
- Confirm after editing (or confirming already-absent): `rg -n "cfg.use_semantic_cache"
  tests/rag/test_rag_http_mode.py` returns zero matches.

## Compatibility considerations
N/A: test-only file.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file — coordinate with `semcacherm`'s
  procedure document `18`'s revert state, same as procedure document `33`.

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py -v` — all tests pass.
- `rg -n "cfg.use_semantic_cache" tests/rag/test_rag_http_mode.py` — zero matches.

## Completion criteria
- `cfg.use_semantic_cache = False` no longer appears in this file, whether removed by
  this document or already absent due to `semcacherm`'s procedure document `18` having
  landed first (Plan `AC-8`).

## Out of scope
- `pipeline.semantic_cache = MagicMock()` (owned by `semcacherm`'s procedure document
  `18`).
- Every other line in `_make_pipeline()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Check for `semcacherm` procedure `18` overlap first — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixture cleanup only |
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
- **Requirement ID**: `REQ-009` (remove cache references from mocks and fixtures)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/rag/test_rag_http_mode.py
