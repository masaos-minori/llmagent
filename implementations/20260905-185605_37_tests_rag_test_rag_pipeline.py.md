## Goal
Remove `use_semantic_cache`/`semantic_cache_max_size`/`semantic_cache_threshold`
fixture keys from `tests/rag/test_rag_pipeline.py`'s two `SimpleNamespace` config
fixtures, made obsolete by procedure documents `01`/`03` (`REQ-009`).

## Scope
- **In-Scope**: two occurrences of the same three-key block: `use_semantic_cache=False,`
  (line 178), `semantic_cache_max_size=0,` (line 184), `semantic_cache_threshold=0.0,`
  (line 185); and a second occurrence at `use_semantic_cache=False,` (line 258),
  `semantic_cache_max_size=0,` (line 264), `semantic_cache_threshold=0.0,` (line 265).
- **Out-of-Scope**: a *third* occurrence of this same three-key pattern at lines
  342/348-349 — this falls inside `class TestInvalidateCache`'s `_make_pipeline()`
  helper, which the `semcacherm` Plan's own procedure document `08`
  (`implementations/20260905-165123_08_tests_rag_test_rag_pipeline.py.md`) deletes in
  its entirety (lines 329-398, the file's exact final section) — do not edit those
  three lines here, since the whole enclosing class is removed by that document, not
  edited by this one. Every other line in both `SimpleNamespace` fixtures — confirmed
  unrelated by reading the surrounding context.

## Assumptions
- **Cross-Plan overlap** (per Step 3a Adversarial Verification, same pattern as
  procedure documents `33`/`34`): the Plan's own Repository Evidence for this row
  ("`rg -c` match count 9") counts all three occurrences (9 lines = 3 lines × 3
  occurrences) without distinguishing that one occurrence (lines 342/348-349) sits
  inside a class the `semcacherm` Plan deletes wholesale. This document's scope is
  narrowed to the two occurrences (lines 178/184-185, 258/264-265) outside that
  deleted class — editing the third occurrence here would be redundant with, and
  race against, `semcacherm` procedure document `08`'s whole-class deletion.
- These fixtures are `SimpleNamespace` objects (not real `RAGConfig`/`RagConfigImpl`
  instances) — confirmed by reading the surrounding constructor calls — so removing
  these keys does not strictly require `RAGConfig`/`RagConfigImpl`'s own field removal
  to land first (a `SimpleNamespace` accepts arbitrary keyword arguments regardless);
  however, the resulting pipeline instance's `._cfg.use_semantic_cache` attribute
  access in `scripts/rag/pipeline.py` (procedure document `01`'s target, in the
  `semcacherm` Plan) would still be gone from `RagPipeline`'s own code by then, making
  the keys' presence or absence in the fixture immaterial to production behavior
  either way — removing them here is purely fixture hygiene, not required for test
  correctness.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Edit only the two occurrences outside `class TestInvalidateCache` — the third
  occurrence's enclosing class is deleted wholesale by a different Plan's procedure
  document; duplicating that deletion's effect here on three specific lines inside a
  soon-to-be-deleted class adds no value and risks an edit-then-delete race if the two
  procedure documents are applied out of order.

## Alternatives considered
- Editing all three occurrences (matching the Plan's literal "9 matches" evidence) —
  rejected: the third occurrence is inside a class scheduled for whole-class deletion
  by `semcacherm` procedure document `08`; editing three lines inside a class about to
  be deleted is wasted work at best and a source of merge/ordering confusion at worst.

## Implementation
### Target file
`tests/rag/test_rag_pipeline.py`

### Procedure
1. Remove `use_semantic_cache=False,` (line 178), `semantic_cache_max_size=0,` (line
   184), and `semantic_cache_threshold=0.0,` (line 185) from the first
   `SimpleNamespace` fixture.
2. Remove `use_semantic_cache=False,` (line 258), `semantic_cache_max_size=0,` (line
   264), and `semantic_cache_threshold=0.0,` (line 265) from the second
   `SimpleNamespace` fixture.
3. Do not edit lines 342/348-349 — confirm they fall inside `class
   TestInvalidateCache`, which `semcacherm` procedure document `08` removes wholesale;
   if that document has already run, confirm these lines (and the whole class) are
   already absent rather than re-editing them.

### Method
Direct removal via `Edit` for the two in-scope occurrences; a presence check (not an
edit) for the third, out-of-scope occurrence.

### Details
- Re-read the file's current class boundaries immediately before editing (per Step 3a
  Adversarial Verification) to confirm which occurrence is inside vs. outside
  `TestInvalidateCache`, since line numbers may have shifted if `semcacherm`'s
  procedure document `08` (or any other prior edit) has already run in this
  implementation pass.
- Confirm after editing: `rg -n "semantic_cache" tests/rag/test_rag_pipeline.py`
  returns zero matches if `semcacherm` procedure document `08` has also completed (the
  third occurrence would be gone via that deletion); if `08` has not yet run, exactly
  3 matches remain (the third occurrence, inside the still-present
  `TestInvalidateCache` class) — do not treat this as a failure of this document's own
  scope.

## Compatibility considerations
N/A: test-only file.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; coordinate with `semcacherm`
  procedure document `08`'s state (see Details) to avoid reintroducing a partially
  reverted file.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py -v` — all tests pass (or, if
  `semcacherm` procedure document `08` has not yet run, all tests except
  `TestInvalidateCache`'s four tests, which are that document's own concern).
- `rg -n "semantic_cache" tests/rag/test_rag_pipeline.py` — zero matches once both
  this document and `semcacherm` procedure document `08` have completed.

## Completion criteria
- The two in-scope occurrences (lines 178/184-185, 258/264-265) no longer reference
  any of the three removed keys (Plan `AC-1`, `AC-8`).

## Out of scope
- The third occurrence inside `class TestInvalidateCache` (owned by `semcacherm`
  procedure document `08`, which deletes the whole class).
- Every other test in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Two occurrences only — see Scope/Out-of-Scope |
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
- **Related target files**: tests/rag/test_rag_pipeline.py
