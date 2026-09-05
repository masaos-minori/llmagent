## Goal
Remove the `use_semantic_cache`/`semantic_cache_max_size`/`semantic_cache_threshold`
rows and the `semantic_cache_max_size` cross-reference-note mention from
`docs/03_rag_05_1-configuration-reference.md`, since these config keys no longer exist
once `semcacheconfig` lands (`REQ-003`).

## Scope
- **In-Scope**: remove three rows from the Agent config table (line 98:
  `| \`use_semantic_cache\` | \`false\` | Whether to use SemanticCache |`; line 99:
  `| \`semantic_cache_max_size\` | \`128\` (code default; operational config uses
  \`100\`) | SemanticCache capacity |`; line 100: `| \`semantic_cache_threshold\` |
  \`0.92\` | Cosine similarity threshold for cache hit detection |`); remove
  `semantic_cache_max_size` from the "Implementation Supplements" cross-reference
  note's parameter list (line 112); remove two rows from the RAG MCP config table
  (line 134: `| \`semantic_cache_max_size\` | SemanticCache capacity (0 = immediate
  eviction/effectively disabled, negative = validation error) |`; line 135: `|
  \`semantic_cache_threshold\` | Cosine similarity threshold for cache hit detection
  |`).
- **Out-of-Scope**: every other row in both config tables (`use_rrf`, `use_rerank`,
  `use_refiner`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`,
  `max_chunks_per_doc`, `refiner_*`, `mqe_*`, `rerank_prompt_template`,
  `rag_service_url`) — confirmed unrelated by reading both tables in full; the
  cross-reference note's remaining parameters (`top_k_search`, `top_k_rerank`,
  `rag_min_score`, `refiner_max_chars_per_chunk`) — confirmed unrelated; the
  `## 1.5 config/agent.toml` section and every other section of this document.

## Assumptions
- `RagConfigImpl`/`RAGConfig`/`RagPipelineConfig` (`semcacheconfig`'s procedure
  documents `01`/`03`/`06`) no longer declare these three fields by the time this
  document's edit lands — this document must describe the *current* configuration
  contract, not a stale one.
- The "Implementation Supplements" cross-reference note (line 112) states a
  code-vs-operational-TOML default-value mismatch for five named parameters —
  removing `semantic_cache_max_size` from that list leaves four (`top_k_search`,
  `top_k_rerank`, `rag_min_score`, `refiner_max_chars_per_chunk`); this document does
  not re-verify whether those four still have a genuine mismatch (out of this Plan's
  scope — that note's accuracy for the remaining parameters is a pre-existing claim
  this Plan does not re-derive).

## Design decisions
(per `skills/DESIGN.md` Output language / `skills/python-documentation` conventions)
- Remove each row/mention cleanly rather than marking it "removed" or "deprecated" in
  place — the originating issue and this Plan's scope is deletion of stale
  configuration documentation, not a deprecation-tracking note (no active
  configuration key exists to deprecate; the key itself is gone).
- Leave the RAG MCP config table's two-column format (no `Default` column, unlike the
  Agent table) unchanged for its remaining rows — that structural difference between
  the two tables predates and is unrelated to this Plan.

## Alternatives considered
N/A: straightforward removal of six now-stale documentation references (three rows,
one cross-reference-note item, two rows) with no remaining subject to describe.

## Implementation
### Target file
`docs/03_rag_05_1-configuration-reference.md`

### Procedure
1. Remove the three Agent-config-table rows for `use_semantic_cache`,
   `semantic_cache_max_size`, `semantic_cache_threshold` (lines 98-100).
2. In the "Implementation Supplements" cross-reference note (line 112), remove
   `semantic_cache_max_size` from the comma-separated parameter list — result:
   "`top_k_search`, `top_k_rerank`, `rag_min_score`, and `refiner_max_chars_per_chunk`".
3. Remove the two RAG-MCP-config-table rows for `semantic_cache_max_size`,
   `semantic_cache_threshold` (lines 134-135).

### Method
Direct `Edit`: three table-row removals and one list-item removal within a
cross-reference note's prose.

### Details
- Confirm the cross-reference note's grammar remains correct after removing one item
  from a five-item list (e.g. "the following parameters—A, B, C, and D—" not "A, B,
  C, D, and" with a dangling comma).
- Confirm after editing: `rg -in "semantic.cache|semantic_cache"
  docs/03_rag_05_1-configuration-reference.md` returns zero matches.

## Compatibility considerations
N/A: documentation-only change; no code consumer.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of every other procedure
  document in this Plan.

## Validation plan
- `uv run python tools/check_docs_quality.py` — no new findings (table structure
  intact after row removal).
- `uv run python tools/check_docs_structure.py
  docs/03_rag_05_1-configuration-reference.md` — passes.
- `uv run python tools/check_docs_consistency.py --domain rag` — passes; confirms no
  stale config-key cross-reference remains (this checker's `tooldrift`/config-key
  checks, per `rules/toolchain.md`).

## Completion criteria
- No row or cross-reference-note mention of `use_semantic_cache`,
  `semantic_cache_max_size`, or `semantic_cache_threshold` remains in this document
  (Plan `AC-3`, `AC-4`).
- All three documentation checkers listed in Validation plan pass.

## Out of scope
- Every other row/parameter in both config tables.
- `config/rag_pipeline_mcp_server.toml` itself (`semcacheconfig`'s procedure document
  `10`).
- `## 1.5 config/agent.toml` and every other section of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacheconfig` implementation lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document's Implementation IS the documentation update |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacheconfig`'s implementation landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (remove the three semantic-cache config rows and cross-reference note)
- **Source issue**: issues/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-192023
- **Related target files**: docs/03_rag_05_1-configuration-reference.md
