## Goal
- Restore the invariant that an English chunk's stored `content` is the original crawled text region (not a stopword-stripped projection), and set English `normalized_content` to `NULL` (Shape B, filtering dropped) per the owner decision recorded in `ADR-009`, changing only the English chunking path.

## Priority
High

## Scope
- **In-Scope**:
  - Store the unfiltered crawled English text region as the chunk `content` in `scripts/rag/ingestion/chunk_english.py`.
  - Set English `normalized_content` to `NULL` (Shape B, filtering dropped) in
    `scripts/rag/ingestion/chunk_splitter.py`, matching the owner decision recorded in
    `ADR-009` (INV-04: English/code/non-normalized text gets `normalized_content = NULL`).
  - Keep the `min_chunk` discard decision on the same measurement basis the current code uses, and document that basis.
  - Add the first test asserting both `content` and `normalized_content` for a non-empty `en_stopwords` configuration.
  - Document exactly what English `content` and `normalized_content` contain.
  - Record the owner decision in `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` as an invariant or an explicit exception, with the tradeoff.
- **Out-of-Scope**:
  - Japanese normalization behavior and its Sudachi normalization.
  - Code-block chunking (`_chunk_code`).
  - Stopword-list contents or chunk-size constants (`en_stopwords`, `_min_chunk`, `_max_chunk`, `_chunk_overlap`) — do not adjust them.
  - Chunk size tuning.
  - Regenerating or re-embedding existing production chunks (recorded as a manual deployment step, not part of the code change).
- **Dependencies**: `N/A: none`
  - **Depends on**: `issues/20261119-112014_ragcrv002_english-content-stopword-loss.md` | phase `all` | the owner decision on the English normalization shape is a BLOCKING Unknown that must be resolved before any code change (recorded as UNK-01)

## Background
`ADR-009` defines `chunks.content` as the canonical, original readable text used for the LLM Context and `chunks.normalized_content` as derived search text indexed only by FTS5 via `COALESCE(normalized_content, content)`. INV-01 states `content` is the original readable text; INV-04 states English/code/non-normalized text gets `normalized_content = NULL`, falling back to `content`; INV-02 states `normalized_content` is used only for FTS5; INV-06 states the original is not restored from `normalized_content`; the ADR also records that the embedding is computed from `content`. The Japanese path honors this invariant: `content` carries the original text and `normalized_content` carries the Sudachi-normalized projection.

## Problem
For English, `ChunkEnglishMixin._chunk_english` maps every merged chunk through `_filter_stopwords_en` and keeps only the filtered strings; `_build_text_triples` writes them as `("text", c, "")` and `_build_chunk_payload` stores the empty normalized value as `NULL`. So an English `chunk.content` is a lossy, stopword-stripped derivative of the crawled page, and `normalized_content` is `NULL`, so nothing preserves the original either. The LLM context, the embedding, and the FTS5 fallback all read that projection, and the crawled original cannot be recovered without a re-crawl. This contradicts INV-01/INV-05/INV-06 and the Japanese path the ADR describes.

## Reason for Change
RAG output quality and index consistency depend on which text is authoritative. The behavior is currently undocumented and untested in a way that distinguishes intent from defect, so it cannot be confirmed as intentional. The contradiction with the documented invariants must be resolved either by restoring the invariant or by recording an explicit exception.

## Implementation Intent
Change only the English chunking path. Make `content` the unfiltered crawled text region for English. Set English `normalized_content` to `NULL` (Shape B, filtering dropped) so English behaves like code/markdown under INV-04; FTS5 then indexes the original `content` via `COALESCE(normalized_content, content)`. Shape A (the stopword-stripped projection, so FTS5 indexes the stripped text while `content` stays original) was considered and rejected: ADR-009 INV-04 already dictates `NULL` for English, and no FTS quality measurement exists to favor keeping the projection. The owner decision (Shape B) is recorded in the Unknowns resolution below and must be written into `ADR-009` during implementation (REQ-008). Keep embeddings computed from `content` per ADR-009. Do not implement both shapes. Do not touch the Japanese path or stopword-list/chunk-size constants.

## Requirements
- `REQ-001`: An English chunk's stored `content` equals the crawled text region it came from (whitespace-normalized) with no words removed.
- `REQ-002`: English `normalized_content` is `NULL` (Shape B, filtering dropped), matching the owner decision recorded in `ADR-009` (INV-04).
- `REQ-003`: Embeddings keep being computed from `content`, per ADR-009 INV-02.
- `REQ-004`: The Japanese path and its Sudachi normalization are unchanged.
- `REQ-005`: The `min_chunk` discard decision keeps the same measurement basis the current code uses, and that basis is documented.
- `REQ-006`: The first test asserting both `content` and `normalized_content` for a non-empty `en_stopwords` configuration exists and passes.
- `REQ-007`: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` states exactly what English `content` and `normalized_content` contain.
- `REQ-008`: `ADR-009` records the decision as an invariant or an explicit exception, with the tradeoff.

## Implementation Target Files
**Freeze status**: Frozen (set 20261119-130500 after `issue-to-plan` Step 8
Implementation Target Files Validation passed; every row `Verified`, no path in both
`Implementation Target Files` and `Reference Files`, no directory/glob/group row).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_english.py` | Modify | `_chunk_english` must return the unfiltered English text region as `content`; `_filter_stopwords_en` result feeds only `normalized_content` (shape A) or is dropped (shape B) | REQ-001, REQ-002, REQ-005 | `_chunk_english` maps every merged chunk through `_filter_stopwords_en` and keeps only filtered strings (chunk_english.py:30-31); `_filter_stopwords_en` defined at chunk_english.py:83 | `tests/rag/ingestion/test_chunk_splitter.py` | Verified (Step 3) |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | `_build_text_triples` must emit the unfiltered English text as the `content` triple and the chosen projection as `normalized_content`; `_build_chunk_payload` already stores `norm_content or None` | REQ-001, REQ-002 | `_build_text_triples` returns `[("text", c, "") for c in self._chunk_english(content)]` (chunk_splitter.py:292); `_build_chunk_payload` stores `"normalized_content": norm_content or None` (chunk_splitter.py:389) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified (Step 3) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Add the first test asserting both `content` and `normalized_content` for a non-empty `en_stopwords` configuration | REQ-006 | No existing test asserts the stored English `content`/`normalized_content` values; `_CRAWL_CONFIG` supplies a non-empty `en_stopwords` list (test:405-...) but no assertion pins the stored values | `tests/rag/ingestion/test_chunk_splitter.py` | Verified (Step 3) |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Document exactly what English `content` and `normalized_content` contain and the `min_chunk` measurement basis | REQ-005, REQ-007 | Current doc describes stopword removal only as the discard threshold and does not state that the stored text is filtered | `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Verified (Step 3) |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Record the owner decision as an invariant or an explicit exception with the tradeoff | REQ-008 | ADR INV-01/02/04/06 wording matches the issue (adr lines 158-163); "Current Decision Approval (pending)" — approver/date not recorded (adr line 279) | Verified (Step 3) | Verified (Step 3) |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/embedding.py` | `embed_and_store()` computes the embedding from `content` (line 91); confirm the change keeps embeddings on the original text | REQ-003 |
| `scripts/rag/ingestion/chunk_japanese.py` | Confirm the Japanese path is structurally independent so the change stays English-only | REQ-004 |
| `scripts/rag/ingestion/chunk_utils.py` | `start_next_buf`/`merge` helpers used by the English merger; read to preserve merge/split semantics | REQ-001 |
| `tests/rag/test_fts_fallback.py`, `tests/rag/test_fts_sync.py` | Existing FTS tests that must stay green after the change (issue Testing Expectations) | REQ-002 |

## Acceptance Criteria
- For an English source, the written chunk `content` equals the crawled text region it came from (whitespace-normalized), with no words removed. (REQ-001)
- `normalized_content` is `NULL` (Shape B, filtering dropped), matching the owner decision recorded in `ADR-009`. (REQ-002)
- Embeddings are still computed from `content`, not `normalized_content`. (REQ-003)
- The Japanese path and its Sudachi normalization are byte-for-byte unchanged. (REQ-004)
- The `min_chunk` discard decision uses the same measurement basis as before, stated in the docs. (REQ-005)
- A new test asserts both `content` and `normalized_content` for a non-empty `en_stopwords` configuration. (REQ-006)
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` states exactly what English `content` and `normalized_content` contain. (REQ-007)
- `ADR-009` records the decision as an invariant or an explicit exception, with the tradeoff. (REQ-008)

## Tests
- Unit: `_chunk_english` with a non-empty `en_stopwords` list returns the original text region as `content` and the chosen `normalized_content` shape. (REQ-001, REQ-002, REQ-006)
- Unit: `_build_text_triples` maps the English projection to the correct payload field (`content` vs `normalized_content`). (REQ-002)
- Integration: existing `tests/rag/test_fts_fallback.py` and `tests/rag/test_fts_sync.py` stay green. (REQ-002, REQ-007)
- Regression: `TestChunkPayloadKeyContract` stays green. (REQ-002)
- Regression: the Japanese chunking tests stay green, confirming REQ-004. (REQ-004)

## Documentation Impact
`docs/*.md` must be updated for this Plan. `REQ-007` drives updating the ChunkSplitter detail doc via `docs/00_index.md`'s "Document References by Task" table (task `rag` → `rag_02_03_ingestion_pipeline-chunksplitter.md`), stating exactly what English `content` and `normalized_content` contain. `REQ-008` drives recording the owner decision in the RAG FTS5 text-separation ADR via `docs/00_index.md` (area `governance` → `adr_02_06_009_rag-fts5-text-separation.md`). `docs/21_rag/rag_05_01-configuration-reference.md` should state what `en_stopwords` actually affects if the doc currently implies it controls stored `content`.

## Assumptions
- The two shapes differ only in the value written to English `normalized_content`; both keep `content` as the original text, which ADR-009 INV-01 already mandates.
- `normalized_content` is populated solely through `_build_text_triples`/`_build_chunk_payload`; no other writer sets it for English chunks.
- The `min_chunk` discard basis is `len(c)` over the post-filter string; the plan preserves whatever basis the current code measures, and the docs will state it explicitly rather than assume.
- Changing `content` changes embeddings, so existing production chunks require re-chunking and re-embedding; this is a manual deployment step outside the code change.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner decision on the English normalization shape: is English `normalized_content` the stopword-stripped projection (filtering kept, FTS5 indexes it) or `NULL` (filtering dropped)? The issue's AI Implementation Instruction says "confirm the owner's decision first"; no rationale was found in the docs and no FTS quality measurement exists to favor either shape. | An owner/approver decision recorded on ADR-009 (its "Current Decision Approval (pending)" at adr line 279 had no approver or date). | RESOLVED 20261119-130500 by owner: Shape B (`NULL`, filtering dropped), because ADR-009 INV-04 already dictates `NULL` for English and no FTS measurement favors keeping the projection. Decision must be written into `ADR-009` during implementation (REQ-008). Resume at Step 8 to freeze and archive the Issue. | False |
| UNK-02 | Whether production English chunks must be regenerated in the same release as the fix. | No policy found linking a `content` change to a mandatory re-chunk/re-embed release. | State as a deployment prerequisite in the Plan's deployment step; non-blocking for the code change. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_english.py` | Modify | High | Low (not in last 30 days top churn) | Single author repo — confirm via `git-fame` if installed | Not directly deployed; re-chunk/re-embed is a manual RAG step |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | High | 6 (in last 30 days) | Single author repo — confirm via `git-fame` if installed | Not directly deployed; re-chunk/re-embed is a manual RAG step |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Medium | N/A | N/A | None |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Low | N/A | N/A | None |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Low | N/A | N/A | None |

## Design
**Path B classification.** This is a Path B task: more than three files would need modification (`chunk_english.py`, `chunk_splitter.py`, a new/updated test, two docs), the change alters a runtime/data value (`content`) that feeds the embedding and FTS5 index, and it leaves a design choice open. All four Path B analyses were performed: architecture (`chunk_english.py` imports only `re` and `chunk_utils`; narrow), dependency graphing (only `chunk_splitter.py` imports `chunk_english`; `_filter_stopwords_en` is called only inside `chunk_english.py`; `embedding.py:embed_and_store` reads `content`), historical analysis (`chunk_splitter.py` churn 6 in 30 days, `chunk_english.py` low churn), and operational inspection (no network ports; no DDL change — `normalized_content` already exists and is NULL for English, so `rules/persisted-schema-change.md` does not apply).

**Validation-quality baseline (Step 5).** `radon cc` on both targets: methods range A(1)-A(5); `_build_text_triples`, `_prune_stale_chunk_files`, `process_file` are B(7). `vulture --min-confidence 80` exit 0 (no dead code). `bandit` 0 issues at all severities/confidence. `diff-cover` against `master` (>= 90%) runs in the implementation-phase gate via `tools/run_validation_gates.py`; this baseline requires the full suite (~3 min) and is documented here rather than run during the document-only phase.

**Two shapes, one decision (locked to Shape B).** Both shapes set English `content` to the unfiltered original (mandated by INV-01). They differ only in `normalized_content`:
- Shape A (filtering kept): `normalized_content` = the stopword-stripped projection. FTS5 indexes `COALESCE(normalized_content, content)` = the stripped text; the LLM context and embedding read the original `content`. This keeps the current search-time behavior but stores a normalized projection.
- Shape B (filtering dropped): `normalized_content` = `NULL`. English then behaves exactly like code/markdown under INV-04; FTS5 indexes the original `content`.

The current code is neither cleanly A nor B: it strips `content` AND writes `NULL` `normalized_content`, so it satisfies INV-04's `NULL` but violates INV-01 by making `content` lossy. **Owner decision (resolved 20261119-130500): Shape B.** Rationale: ADR-009 INV-04 already dictates `NULL` for English/code/non-normalized text, so Shape B restores the documented invariant without an exception, whereas Shape A would require amending INV-04 to carve out an English stopword-filtered exception that no FTS measurement justifies. Shape A is now rejected and must not be implemented.

**Embedding impact.** `embedding.py:embed_and_store` computes `embedding = self.get_embedding(content)` (line 91) and treats `normalized_content` as FTS-only. Restoring original `content` therefore changes every English embedding; existing chunks must be re-chunked and re-embedded. This is why the change is runtime-impacting and classified Path B.

**Release unit.** Phases land together in one commit and cannot be validated alone until the test (REQ-006) asserts the new shape; see Implementation steps.

## Implementation steps
1. **Phase 1: Lock scope (owner decision already made)**
   - [x] UNK-01 resolved by owner (20261119-130500): English `normalized_content` is Shape B (`NULL`, filtering dropped). (REQ-002)
   - [ ] Record the Shape B decision in `ADR-009` as an invariant restatement (INV-04 already covers English → `NULL`) with the rejected-Shape-A tradeoff. (REQ-008)
2. **Phase 2: Restore original `content` for English (Shape B)**
   - [ ] In `chunk_english.py`, make `_chunk_english` return the unfiltered English text region as the stored `content`; `_filter_stopwords_en` is no longer used to build the stored chunk (the min_chunk discard basis is preserved). (REQ-001, REQ-005)
   - [ ] In `chunk_splitter.py`, `_build_text_triples` emits the unfiltered English text as the `content` triple and `NULL` as `normalized_content` (Shape B). (REQ-001, REQ-002)
   - [ ] Confirm `embedding.py` still embeds `content` (unchanged). (REQ-003)
3. **Phase 3: Tests, docs, and verification**
   - [ ] Add the first test asserting both `content` and `normalized_content` for a non-empty `en_stopwords` configuration. (REQ-006)
   - [ ] Update `rag_02_03_ingestion_pipeline-chunksplitter.md` to state exactly what English `content` and `normalized_content` contain and the `min_chunk` basis. (REQ-007)
   - [ ] Run the FTS regression tests (`test_fts_fallback.py`, `test_fts_sync.py`), `TestChunkPayloadKeyContract`, and the Japanese chunking tests. (REQ-002, REQ-004)

### Release units
**Unit**: english-content-stopword-loss | **Phases**: 1, 2, 3 | **Reason**: the shape (UNK-01) must be decided before Phase 2, and the change is only validated once the REQ-006 test asserts the chosen shape in Phase 3; the phases cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `chunk_english.py` `_chunk_english` | Unit: non-empty `en_stopwords` returns original `content` + chosen `normalized_content` | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | New test passes; `content` has no words removed |
| `chunk_splitter.py` `_build_text_triples` / `_build_chunk_payload` | Unit: payload field mapping | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | `content` triple is unfiltered; `normalized_content` matches the shape |
| FTS5 fallback | Integration: FTS tests stay green | `uv run pytest tests/rag/test_fts_fallback.py tests/rag/test_fts_sync.py` | All pass |
| Japanese path | Regression: unchanged | `uv run pytest tests/rag/ingestion/` | Japanese tests pass unchanged |
| diff-cover | Coverage gate | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% on changed lines |

## Risks
- **Risk**: Changing `content` changes every English embedding, so existing production chunks become stale until re-chunked and re-embedded. → **Mitigation**: record a manual deployment step (re-chunk with `chunk_splitter.py --force`, then re-embed) as a prerequisite; the code change itself is correct regardless, and the consistency check flags drift until re-embed completes.
- **Risk**: Choosing the wrong shape (A vs B) degrades FTS5 search quality. → **Mitigation**: UNK-01 was resolved by the owner as Shape B (20261119-130500) because ADR-009 INV-04 already dictates `NULL` for English and no FTS measurement favors keeping the projection; the decision is recorded deliberately and `content` stays original so the LLM context is never lossy under either shape.
- **Risk**: Accidentally altering the Japanese path or stopword-list/chunk-size constants. → **Mitigation**: scope excludes them; REQ-004 regression on Japanese tests and the English-only call graph (`_filter_stopwords_en` only in `chunk_english.py`) bound the change.
- **Risk**: The `min_chunk` discard basis silently changes. → **Mitigation**: REQ-005 preserves the current basis and requires the docs to state it explicitly.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Decide shape and lock scope (owner decision on UNK-01) | Completed | 20261119-130500 | 2026-11-19 | UNK-01 resolved as Shape B (`NULL`); scope locked; Plan Frozen |
| 2 | Restore original `content` for English (Shape B) | Completed | 2026-11-19 | 2026-11-19 | _chunk_english returns unfiltered content (Shape B); verified |
| 3 | Tests, docs, and verification | Completed | 2026-11-19 | 2026-11-19 | new test + doc/ADR updates; ruff+pytest pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01: owner decision on English `normalized_content` shape | True | 20261119-130500 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261119-132013_01_scripts_rag_ingestion_chunk_english.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261119-132013_02_scripts_rag_ingestion_chunk_splitter.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261119-132013_03_tests_rag_ingestion_test_chunk_splitter.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261119-132013_04_docs_21_rag_rag_02_03_ingestion_pipeline-chunksplitter.md.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261119-132013_05_docs_10_adr_adr_02_06_009_rag-fts5-text-separation.md.md` | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-112014_ragcrv002_english-content-stopword-loss.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-123746
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`, `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; `chunk_english.py:30-31` | `scripts/rag/ingestion/chunk_english.py` | Phase 2 | `content` equals crawled region (AC-1) | Unit: `_chunk_english` non-empty stopwords | Confirmed by repository evidence |
| REQ-001 | Problem; `chunk_splitter.py:292` | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | `content` equals crawled region (AC-1) | Unit: `_build_text_triples` | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; ADR INV-04 | `scripts/rag/ingestion/chunk_english.py` | Phase 2 | `normalized_content` is NULL (AC-2) | Unit: payload mapping | Confirmed (Shape B) |
| REQ-002 | Implementation Intent; ADR INV-04 | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | `normalized_content` is NULL (AC-2) | FTS fallback tests | Confirmed (Shape B) |
| REQ-003 | ADR INV-02; `embedding.py:91` | N/A: no target modification — `embedding.py` (reference) stays unchanged | Phase 2 | Embeddings from `content` (AC-3) | Regression | Confirmed by repository evidence |
| REQ-004 | Constraints; Japanese path independent | N/A: no target modification — `chunk_japanese.py` (reference) stays unchanged | Phase 2 | Japanese path unchanged (AC-4) | Japanese regression | Confirmed by repository evidence |
| REQ-005 | Required Changes; discard basis | `scripts/rag/ingestion/chunk_english.py` | Phase 2 | `min_chunk` basis preserved + documented (AC-5) | Docs review | Confirmed by repository evidence |
| REQ-006 | Testing Expectations | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 3 | new test asserts both fields (AC-6) | New test | Explicit in issue |
| REQ-007 | Documentation Impact | `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Phase 3 | doc states values (AC-7) | Docs review | Explicit in issue |
| REQ-008 | Constraints; ADR approval pending | `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Phase 1 | decision recorded as invariant/exception (AC-8) | ADR review | Confirmed (Shape B); ADR write is Phase 1 implementation |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261119-132013 -->
