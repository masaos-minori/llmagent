## Goal
Remove `semantic_cache_max_size`/`semantic_cache_threshold`/`use_semantic_cache`
fields/arguments from `tests/rag/test_rag_pipeline_stage.py`'s `_RagCfg` dataclass and
`_make_rag_cfg()`'s `RagConfigImpl(...)` construction, made obsolete by procedure
document `01` (`REQ-001`, `REQ-009`).

## Scope
- **In-Scope**: remove `semantic_cache_max_size: int = 0` (line 23),
  `semantic_cache_threshold: float = 0.0` (line 24), `use_semantic_cache: bool =
  False` (line 25) from `_RagCfg`'s field declarations; remove
  `semantic_cache_max_size=0,` (line 58), `semantic_cache_threshold=0.0,` (line 59),
  `use_semantic_cache=False,` (line 60) from `_make_rag_cfg()`'s `RagConfigImpl(...)`
  construction.
- **Out-of-Scope**: this file's `class TestSemanticCacheDimensionGuard` (a separate,
  unrelated set of lines, removed wholesale by the `semcacherm` Plan's own procedure
  document `09`,
  `implementations/20260905-165123_09_tests_rag_test_rag_pipeline_stage.py.md`) — do
  not touch lines in that class; every other field in `_RagCfg`/`_make_rag_cfg()` —
  confirmed unrelated.

## Assumptions
- `_make_rag_cfg()`'s `base = RagConfigImpl(...)` construction requires
  `RagConfigImpl` (procedure document `01`) to no longer declare the three fields, or
  this construction will raise `TypeError: unexpected keyword argument` after that
  document lands — this document's edit must land no earlier than `01`'s.
- `_RagCfg` (the standalone dataclass, distinct from `RagConfigImpl`) has **no
  confirmed usage anywhere in this file** (`grep -n "_RagCfg\b"` matches only its own
  definition, line 22) — it appears to be pre-existing dead code, unrelated to this
  Plan's scope. This document removes only the three cache fields from its
  declaration (per this Plan's `REQ-009` fixture-cleanup scope), leaving the rest of
  `_RagCfg` and the question of its overall dead-code status untouched, per `AGENTS.md`
  Global Rule 5 (no unrelated cleanup beyond what this task requires).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Edit `_RagCfg`'s field list even though the class itself appears unused — leaving
  stale cache-field declarations in an otherwise-dead class would still reference the
  removed concept by name, which is what `REQ-009`'s fixture-cleanup scope targets;
  removing the whole unused class is a separate, out-of-scope cleanup this document
  does not perform.
- Do not touch `class TestSemanticCacheDimensionGuard` — that class's removal is
  `semcacherm` procedure document `09`'s scope (a different Requirement, a different
  Plan); this document's Requirement Traceability does not cover it.

## Alternatives considered
- Removing `_RagCfg` entirely as apparent dead code — rejected: confirming and acting
  on dead-code status is outside this Plan's `REQ-009` scope (fixture-key cleanup, not
  dead-code removal); flag as a candidate follow-up cleanup instead of performing it
  here.

## Implementation
### Target file
`tests/rag/test_rag_pipeline_stage.py`

### Procedure
1. Remove `semantic_cache_max_size: int = 0` (line 23), `semantic_cache_threshold:
   float = 0.0` (line 24), and `use_semantic_cache: bool = False` (line 25) from
   `_RagCfg`'s field declarations.
2. Remove `semantic_cache_max_size=0,` (line 58), `semantic_cache_threshold=0.0,`
   (line 59), and `use_semantic_cache=False,` (line 60) from `_make_rag_cfg()`'s
   `RagConfigImpl(...)` construction.
3. Do not edit `class TestSemanticCacheDimensionGuard` (owned by `semcacherm`
   procedure document `09`).

### Method
Direct removal via `Edit` in two locations (dataclass field list, constructor call).

### Details
- Confirm `_RagCfg` has no other reader before finalizing (per Assumptions) — if a
  future investigation finds a caller this Plan's evidence missed, treat the field
  removal the same way regardless (the caller would then also need the three fields
  gone from wherever it reads them, which is this Plan's overall intent).
- Confirm after editing: `rg -n "semantic_cache" tests/rag/test_rag_pipeline_stage.py`
  returns zero matches once this document and `semcacherm` procedure document `09`
  have both landed; until `09` lands, matches remain inside
  `TestSemanticCacheDimensionGuard` only (not a failure of this document's own scope).

## Compatibility considerations
N/A: test-only file.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `01` (`RagConfigImpl`); coordinate with `semcacherm` procedure
  document `09`'s state to avoid a partial revert.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline_stage.py -v` — all tests pass (excluding
  `TestSemanticCacheDimensionGuard`'s tests, which are `semcacherm` procedure document
  `09`'s own concern if not yet applied).
- `rg -n "semantic_cache" tests/rag/test_rag_pipeline_stage.py` — see Details for the
  expected match count depending on `09`'s landing state.

## Completion criteria
- `_RagCfg` and `_make_rag_cfg()` no longer reference any of the three removed keys
  (Plan `AC-1`, `AC-8`).

## Out of scope
- `class TestSemanticCacheDimensionGuard` (owned by `semcacherm` procedure document
  `09`).
- Removing `_RagCfg` as apparent dead code (a separate, unperformed cleanup — flagged
  in Alternatives considered).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (fixture constructs `RagConfigImpl` directly with the removed fields)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/rag/test_rag_pipeline_stage.py
