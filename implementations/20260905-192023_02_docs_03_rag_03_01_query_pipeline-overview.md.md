## Goal
Remove the "Semantic Cache" numbered step from the `augment()` fallback-chain
description in `docs/03_rag_03_01_query_pipeline-overview.md`, since that lookup no
longer exists once `semcacherm` lands (`REQ-002`).

## Scope
- **In-Scope**: remove item `2. Semantic Cache: If \`semantic_cache.lookup()\` hits,
  returns string. Otherwise \`None\`.` (line 56) from the `augment()` Fallback Chain's
  numbered list; renumber the remaining four items (HTTP Mode stays `1`; Search
  Pipeline, Refiner, Raw Chunks shift from `3`/`4`/`5` to `2`/`3`/`4`).
- **Out-of-Scope**: the surrounding prose ("`augment()` determines the final result
  through the following sequence...", "**Identity vs Truthiness**", "**On DB
  Connection Failure**") and every other section of this document — confirmed
  unrelated by reading the full file.

## Assumptions
- `RagPipeline.augment()` (`semcacherm`'s procedure document `01`) no longer has a
  cache-lookup branch by the time this document's edit lands — this document
  describes the *current* fallback chain, so it must reflect the code's actual
  post-removal control flow, not a stale intermediate state.

## Design decisions
(per `skills/DESIGN.md` Output language / `skills/python-documentation` conventions)
- Renumber the remaining items to keep the list a clean, sequential `1`-`4` — leaving
  a gap (`1, 3, 4, 5`) or reusing removed number `2` for a different step would
  misrepresent the actual fallback order, which this list exists to document
  precisely ("Each step only falls back to the next if it returns `None`").

## Alternatives considered
N/A: straightforward removal of one obsolete list item with mandatory renumbering to
preserve the list's own stated sequential-fallback semantics.

## Implementation
### Target file
`docs/03_rag_03_01_query_pipeline-overview.md`

### Procedure
1. Remove item `2. Semantic Cache: If \`semantic_cache.lookup()\` hits, returns
   string. Otherwise \`None\`.` (line 56).
2. Renumber the remaining items: `3. Search Pipeline: ...` → `2. Search Pipeline:
   ...`; `4. Refiner: ...` → `3. Refiner: ...`; `5. Raw Chunks: ...` → `4. Raw
   Chunks: ...`. Item `1. HTTP Mode: ...` is unchanged.

### Method
Direct `Edit`: one list-item removal plus renumbering three subsequent items.

### Details
- Confirm the renumbered list still reads as a coherent fallback sequence
  (`1` HTTP Mode → `2` Search Pipeline → `3` Refiner → `4` Raw Chunks) after editing —
  re-read the full "`augment()` Fallback Chain" subsection once more after the edit to
  confirm no other cross-reference in this document cites the old numbering (e.g. "see
  step 3" elsewhere) — none found in this Plan's evidence, but re-verify per Step 3a
  Adversarial Verification.
- Confirm after editing: `rg -in "semantic.cache|semantic_cache"
  docs/03_rag_03_01_query_pipeline-overview.md` returns zero matches.

## Compatibility considerations
N/A: documentation-only change; no code consumer.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of every other procedure
  document in this Plan (this document's content stands alone).

## Validation plan
- `uv run python tools/check_docs_quality.py` — no new findings.
- `uv run python tools/check_docs_structure.py
  docs/03_rag_03_01_query_pipeline-overview.md` — passes.
- `uv run python tools/check_docs_consistency.py --domain rag` — passes.

## Completion criteria
- The "`augment()` Fallback Chain" list no longer mentions Semantic Cache and is
  correctly renumbered `1`-`4` (Plan `AC-3`).
- All three documentation checkers listed in Validation plan pass.

## Out of scope
- Every other section of this document.
- `scripts/rag/pipeline.py`'s `augment()` itself (`semcacherm`'s own procedure
  document `01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Done |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Done |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | This document's Implementation IS the documentation update |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation landing first | Yes | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (remove the Semantic Cache numbered step from the `augment()` flow list)
- **Source issue**: issues/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-192023
- **Related target files**: docs/03_rag_03_01_query_pipeline-overview.md
