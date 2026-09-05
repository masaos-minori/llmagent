## Goal
Remove `TestSemanticCache` (all 8 `SemanticCache(...)` construction sites within it)
from `tests/rag/test_rag_repository.py`, discovered by this Plan's adversarial search
as referencing the removed `SemanticCache` class directly (`REQ-004`).

## Scope
- **In-Scope**: remove the `# ── SemanticCache ──` comment header and
  `class TestSemanticCache:` in their entirety (lines 351-413, including the blank
  line separating the class from the following `# ── deduplicate_chunks ──` section);
  remove `from rag.cache import SemanticCache` (line 16); correct the module
  docstring's class listing (line 2: "Unit tests for rag/repository.py — RagScorer,
  SemanticCache, cosine_sim,") to remove `SemanticCache` from it — an
  adversarial-verification finding not named in the Plan's Repository Evidence for
  this row, but confirmed by this document's own inspection.
- **Out-of-Scope**: `class TestCosineSim`, `class TestRagScorer`,
  `class TestDeduplicateChunks`, `class TestDedupHits`, `class TestRagRepository`,
  `class TestBuildFtsQuery`, `class TestFtsTriggerConcurrency`,
  `class TestRagRepositoryHardening`, `class TestBuildFtsQueryLogging`, and
  `class TestFtsFallback` — confirmed unrelated by reading the full file's class list;
  none references `SemanticCache` outside the removed range (confirmed by
  `awk 'NR>417 && /SemanticCache/'` returning no matches).

## Assumptions
- `scripts/rag/cache.py` (`semcacherm`'s procedure document `02`) is deleted by the
  time this document's edit lands — `from rag.cache import SemanticCache` (line 16)
  would otherwise raise `ImportError` at module-import time for the entire test file
  (not merely the removed class), since it is a module-level import.
- `SemanticCache` has no other reader in this file beyond `TestSemanticCache`'s 8
  construction sites — confirmed by `grep -n "SemanticCache"
  tests/rag/test_rag_repository.py` matching only the docstring, the import, and lines
  within 351-413.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove the module-level import (line 16) together with the class, not separately —
  once `TestSemanticCache` is gone, this import has zero remaining readers in the
  file; leaving it would be a dangling unused import.
- Correct the module docstring's class listing in the same document — per Step 3a
  Adversarial Verification, a stale in-file cross-reference discovered while editing
  the named target is corrected in the same document, matching the precedent set by
  `semcacheconfig`'s procedure document `09` (`cmd_config_display.py`'s docstring
  correction).

## Alternatives considered
N/A: the class under test (`SemanticCache`) no longer exists once `semcacherm` lands;
no adapted version of `TestSemanticCache` is possible.

## Implementation
### Target file
`tests/rag/test_rag_repository.py`

### Procedure
1. Correct the module docstring (line 2) to remove `SemanticCache` from the class
   listing — e.g. "Unit tests for rag/repository.py — RagScorer, SemanticCache,
   cosine_sim," → "Unit tests for rag/repository.py — RagScorer, cosine_sim,".
2. Remove `from rag.cache import SemanticCache` (line 16).
3. Remove the `# ── SemanticCache ──` comment header and `class TestSemanticCache:`
   in their entirety (lines 351-413), including all of its test methods (`grep`
   confirmed 8 `SemanticCache(...)` construction sites across this class's methods).

### Method
Direct `Edit`: one docstring correction, one import removal, one whole-class removal
(with its section-comment header).

### Details
- Confirm the blank-line spacing between the preceding class (`TestRagScorer`, ending
  before line 351) and the following section (`# ── deduplicate_chunks ──`, at what
  was line 414) is left at the file's existing single-blank-line convention after
  removal.
- Confirm after editing: `rg -n "SemanticCache"
  tests/rag/test_rag_repository.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  `semcacherm`'s procedure document `02` (`scripts/rag/cache.py`'s deletion), since
  the removed import and class both depend on that module.

## Validation plan
- `uv run pytest tests/rag/test_rag_repository.py -v` — all remaining tests pass; no
  collection error from a dangling `SemanticCache` import.
- `rg -n "SemanticCache" tests/rag/test_rag_repository.py` — zero matches.

## Completion criteria
- `TestSemanticCache` and its import no longer exist in this file (Plan `AC-1`,
  `AC-2`).
- `uv run pytest tests/rag/test_rag_repository.py -v` passes in full.

## Out of scope
- Every other test class in this file.
- `scripts/rag/cache.py` itself (`semcacherm`'s procedure document `02`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` implementation lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: this document itself is a test-removal change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation (deletes `scripts/rag/cache.py`) landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` (remove `TestSemanticCache` discovered by adversarial search)
- **Source issue**: issues/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-192023
- **Related target files**: tests/rag/test_rag_repository.py
