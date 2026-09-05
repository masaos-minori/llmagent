## Goal
Remove `cfg.use_semantic_cache = False` from `tests/rag/test_pipeline_http_result_kind.py`'s
`_make_pipeline()` fixture, made obsolete by procedure document `03`
(`RAGConfig`'s field removal) (`REQ-009`).

## Scope
- **In-Scope**: remove `cfg.use_semantic_cache = False` (line 21) from
  `_make_pipeline()`.
- **Out-of-Scope**: every other line in `_make_pipeline()` — confirmed unrelated;
  `pipeline.semantic_cache = MagicMock()` (line 29, same function) — this is a
  *different* attribute (the `RagPipeline` instance's own `semantic_cache` attribute,
  not a `cfg` field) already removed by the `semcacherm` Plan's own procedure document
  `17` (`implementations/20260905-165123_17_tests_rag_test_pipeline_http_result_kind.py.md`)
  — see Assumptions for the cross-Plan overlap this creates.

## Assumptions
- **Cross-Plan overlap** (per Step 3a Adversarial Verification): this exact file and
  line (`cfg.use_semantic_cache = False`, line 21) is *also* named in the
  `semcacherm` Plan's own procedure document `17`
  (`plans/done/20260904-140151_plan.md`'s Implementation Target Files row for this
  file), which independently instructs removing the same line (that document's Scope:
  "remove `cfg.use_semantic_cache = False` and `pipeline.semantic_cache =
  MagicMock()` lines"). Both Plans reach this file via different Requirements
  (`semcacherm`'s `REQ-006` "adversarial search" finding vs. this Plan's `REQ-009`
  "repository-wide search match"), but converge on removing the identical line. This
  is not an error in either Plan — whichever procedure document's change lands first
  removes the line; the second document's corresponding step becomes a no-op (the
  line will already be absent). This document's own scope is narrowed to only
  `cfg.use_semantic_cache = False` (not `pipeline.semantic_cache = MagicMock()`,
  which belongs solely to `semcacherm`'s procedure document `17`) to avoid this
  document re-instructing removal of a line outside this Plan's own Requirement
  linkage.
- `cfg` in this fixture is a `MagicMock()` (not a real `RAGConfig`/`RagConfigImpl`
  instance) — removing this line does not depend on procedure document `03`
  (`RAGConfig`) or `01` (`RagConfigImpl`) landing first, since `MagicMock()` accepts
  arbitrary attribute assignment regardless of what any real dataclass declares; this
  document's change is safe to apply independently of those two documents' landing
  order.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Scope this document to exactly the one line this Plan's own Requirement (`REQ-009`)
  covers, leaving `pipeline.semantic_cache = MagicMock()` to `semcacherm`'s own
  procedure document `17` — avoids two procedure documents both claiming ownership of
  the same non-`use_semantic_cache` line under different Plans.

## Alternatives considered
- Removing both lines in this document (duplicating `semcacherm` procedure document
  `17`'s full scope) — rejected: `pipeline.semantic_cache` is a different concept
  (the runtime cache attribute, not a config field) tracked by a different Plan's
  Requirement; this Plan's own Requirement Traceability only supports the config-field
  line.

## Implementation
### Target file
`tests/rag/test_pipeline_http_result_kind.py`

### Procedure
1. Check whether `cfg.use_semantic_cache = False` (originally line 21) is still
   present before editing — if `semcacherm`'s procedure document `17` has already
   removed it (same implementation batch, likely processed first per this Plan's own
   dependency on `semcacherm` landing first), this step is a no-op: confirm via `rg -n
   "cfg.use_semantic_cache" tests/rag/test_pipeline_http_result_kind.py` returning zero
   matches, and record this row as `Already implemented` rather than re-editing.
2. If still present, remove `cfg.use_semantic_cache = False`.

### Method
Direct removal via `Edit`, conditional on presence (see Procedure step 1).

### Details
- Do not remove `pipeline.semantic_cache = MagicMock()` here — that line belongs to
  `semcacherm`'s own procedure document `17`, already applied or pending under that
  Plan's own cycle.
- Confirm after editing (or confirming already-absent): `rg -n "use_semantic_cache"
  tests/rag/test_pipeline_http_result_kind.py` returns zero matches for the `cfg.`-prefixed
  form specifically (a bare `semantic_cache` match on `pipeline.semantic_cache` is
  `semcacherm`'s own concern, not re-checked here).

## Compatibility considerations
N/A: test-only file.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file — coordinate with whichever of the two
  Plans' procedure documents (this one, or `semcacherm`'s `17`) was applied later, to
  avoid a partial revert leaving the file in neither Plan's intended end state.

## Validation plan
- `uv run pytest tests/rag/test_pipeline_http_result_kind.py -v` — all tests pass
  (unaffected either way, since `cfg`/`pipeline` are both `MagicMock()`-backed and
  never asserted on for these specific attributes).
- `rg -n "cfg.use_semantic_cache" tests/rag/test_pipeline_http_result_kind.py` — zero
  matches.

## Completion criteria
- `cfg.use_semantic_cache = False` no longer appears in this file, whether removed by
  this document or already absent due to `semcacherm`'s procedure document `17` having
  landed first (Plan `AC-8`).

## Out of scope
- `pipeline.semantic_cache = MagicMock()` (owned by `semcacherm`'s procedure document
  `17`).
- Every other line in `_make_pipeline()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Check for `semcacherm` procedure `17` overlap first — see Assumptions |
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
- **Related target files**: tests/rag/test_pipeline_http_result_kind.py
