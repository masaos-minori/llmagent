# Plan Japanese chunking emits an empty chunk that breaks the completion sentinel

## Goal
Stop the Japanese chunker from emitting an empty chunk when the first sentence of a document exceeds `max_chunk`, which writes an empty `{stem}-0000.json` sentinel and drives a repeating chunk → quarantine → re-chunk cycle.

## Priority
High

## Scope
- **In-Scope**:
  - Make `ChunkJapaneseMixin._merge_ja_sentence_pairs` never emit a chunk pair whose original text is empty.
  - Segment an oversized first Japanese sentence so no emitted pair exceeds `max_chunk`, reusing the shared `_split_overlong` rule instead of a Japanese-specific splitter.
  - Add a regression test for the empty-buffer / oversized-first-sentence case.
  - Document the Japanese oversized-sentence rule and the non-empty-content guarantee.
- **Out-of-Scope**:
  - Unifying the three merge implementations (`issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`).
  - Configuration validation of `min_chunk`/`max_chunk`/`chunk_overlap` (`issues/20261119-112015_ragcrv003_chunk-config-validation.md`).
  - English `content` stopword behavior (`issues/20261119-112014_ragcrv002_english-content-stopword-loss.md`).
  - Re-tuning `min_chunk`, `max_chunk`, `chunk_overlap` values.
  - Changing the English, code-block, or Markdown-heading chunk paths.
- **Dependencies**:
  - `N/A: none` — no open Plan or Issue must complete before this one. See the sequencing note in `Assumptions` about the sibling merger-unification issue.
  - **Depends on**: (none)

## Background
`ChunkSplitter.process_file` treats `{stem}-0000.json` as its completeness sentinel (`pipeline_utils.is_already_processed`) and `ChunkSplitter.publish_chunk_files` publishes the `-0000` file last, so its presence is the only completeness signal for a chunk set. The buffer-retain branch in `ChunkJapaneseMixin._merge_ja_sentence_pairs` (added by `issues/done/20261107-060510_ragc002_ja-sentence-merge-content-loss.md`) appends the current buffer before starting a new one. When the buffer is still empty because the first sentence is longer than `max_chunk`, the appended pair is `("", None)`. That empty original is written as `{stem}-0000.json`; the ingester quarantines it (`read_chunk_json` raises `ChunkFormatError` on empty `content`, `ChunkGroupingStrategy.group` rejects it as `parse_failed`, `FileRouter.route` moves it to `failed/`), the sentinel disappears, and the next `process_file(force=False)` re-chunks the same document.

## Problem
An oversized first Japanese sentence produces a chunk whose original text is empty. That file can never be ingested, consumes `chunk_index` 0, becomes the sentinel, and produces a repeating chunk → quarantine → re-chunk cycle that re-embeds the valid chunks of the same document on every run.

## Reason for Change
The loop is silent (only an INFO "chunked N chunks" line and one WARNING per run) and repeats embedding cost for every affected document. It is a residual gap of the already-closed ragc002 fix, not a new design.

## Implementation Intent
Give the Japanese merger the same oversized-item contract the shared helper already implements: an item longer than `max_chunk` is segmented (the strategy `chunk_utils._split_overlong` applies inside `merge_text_items`), and no chunk is ever emitted from an empty buffer. Keep sentence splitting in the Japanese chunker and the segmentation rule in the shared helper so the two paths cannot drift again. The empty-buffer guard and the oversized-segmentation both live in `_merge_ja_sentence_pairs`; `_split_overlong` in `chunk_utils.py` is reused unchanged.

## Requirements
- `REQ-001`: `_merge_ja_sentence_pairs` MUST NOT append a pair whose original text is empty to the result (empty buffer never emits).
- `REQ-002`: An input sentence whose length exceeds `max_chunk` MUST be segmented into pieces each within `max_chunk` using the shared `_split_overlong` rule, so no emitted pair exceeds `max_chunk` without a documented exception.
- `REQ-003`: The emitted `chunk_index` series for one document stays contiguous from 0 and index 0 always carries non-empty original text (the sentinel is consumable).
- `REQ-004`: Sentences whose Sudachi normalization yields nothing keep `normalized_content = None` (COALESCE fallback to the original text).
- `REQ-005`: A regression test asserts a single oversized first sentence emits no empty pair and no oversized pair.
- `REQ-006`: The retention behavior in `TestJapaneseMergeRetention` is preserved (a short sentence that cannot join an oversized next sentence stays retained).
- `REQ-007`: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` states the Japanese oversized-sentence rule and that a written chunk file always carries non-empty content.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | Fix `_merge_ja_sentence_pairs` empty-buffer emission and oversized segmentation | REQ-001, REQ-002, REQ-003, REQ-004 | else-branch emits `(self._orig_buf, ...)` even when empty; `_split_overlong` unused by JA path (checked in Step 3) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Add empty-buffer / oversized-first-sentence regression test; assert retention preserved | REQ-005, REQ-006 | `test_short_lead_before_oversized_is_retained` covers only the non-empty short-buffer case (checked in Step 3) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Document JA oversized-sentence rule and non-empty-content guarantee | REQ-007 | doc exists; no ADR change expected (checked in Step 3) | `N/A` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` | Holds the shared `_split_overlong` greedy segmentation rule reused by REQ-002; confirm its contract is unchanged | `scripts/rag/ingestion/chunk_japanese.py` / REQ-002 |
| `scripts/rag/ingestion/chunk_splitter.py` | Sentinel handling (`is_already_processed`), `publish_chunk_files` descending-index publish order, `chunk_index` assignment | REQ-003 |
| `scripts/rag/ingestion/pipeline_utils.py` | `is_already_processed` sentinel semantics for `{stem}-0000.json` | REQ-003 |

## Acceptance Criteria
- A document whose first Japanese sentence exceeds `max_chunk` produces zero empty chunk files (REQ-001, REQ-003).
- Every emitted Japanese chunk satisfies `len(content) <= max_chunk`, or the exception is documented in `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (REQ-002, REQ-007).
- After one ingestion pass, `{stem}-0000.json` is no longer present in `chunk/` and a following `process_file(force=False)` returns 0 with a "skip (already chunked)" log line (REQ-003).
- `TestJapaneseMergeRetention`, `TestJapaneseChunkOverlap`, `TestAtomicChunkWrite` stay green (REQ-006).
- Existing chunk tests stay green (REQ-005).

## Tests
- Unit: `_merge_ja_sentence_pairs` with a single oversized first sentence emits no empty pair and no oversized pair (REQ-005, REQ-001, REQ-002).
- Unit: parameterized oversized-first-sentence cases for `min_chunk < max_chunk` and `min_chunk` close to `max_chunk` (REQ-005).
- Integration: `ChunkSplitter.process_file` + `ChunkGroupingStrategy.group` + `FileRouter.route` for a Japanese document with an oversized first sentence — assert nothing lands in `failed/` and the sentinel is consumable (REQ-003).
- Regression: `TestJapaneseMergeRetention`, `TestJapaneseChunkOverlap`, `TestAtomicChunkWrite` stay green (REQ-006).

## Documentation Impact
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (named via `routing.md` Docs → task mapping, RAG domain): state the Japanese path's oversized-sentence rule and that a written chunk file always carries non-empty content. No ADR change expected; if the emission rule changes materially, note it in the ADR-009 Implementation Notes. Driven by REQ-007.

## Assumptions
- The oversized sentence is split at character level via the existing shared `_split_overlong` (raw slicing), matching the issue's stated intent to reuse the shared helper and keep the segmentation rule language-independent.
- Split sub-parts carry `normalized_content = None` so COALESCE falls back to the original text; morphological normalization is not recomputed per sub-part (the sentence was already split at clause boundaries by `_split_into_ja_sentences`).
- `chunk_index` contiguity and last-`-0000` publish order are preserved by the existing `publish_chunk_files`/`process_file` machinery and need no change.
- Sequencing: the sibling issue `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md` later unifies the three mergers and removes the duplicated `_merge_ja_sentence_pairs`. This Plan lands first and is compatible with that follow-up; if an overlap on `scripts/rag/ingestion/chunk_japanese.py` is judged conflicting, the order is the owner's decision.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any production source in `/opt/llm/rag-src` actually contains a Japanese sentence longer than `max_chunk` with no `。！？` or newline boundary | corpus / `chunk.log` inspection | Post-deployment check of `chunk.log`; not required to implement the defensive fix | False |
| UNK-02 | Whether character-level segmentation of an oversized Japanese sentence is acceptable for text quality, or the sentence must be split at Sudachi clause boundaries instead | owner decision on Japanese text quality | Owner decision before implementation; plan assumes character-level via shared helper | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | Low | N/A | N/A | No deploy.sh action required (code-only bugfix; no runtime/config change) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Low | N/A | N/A | No deploy.sh action required (test-only) |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Low | N/A | N/A | No deploy.sh action required (doc-only) |

## Design
Path A (≤ 3 files, no public/runtime interface change, no schema change). Direct verification only (Step 3); no architecture/dependency graphing.

Current `_merge_ja_sentence_pairs` loop:
```python
for orig, norm in pairs:
    norm_str = norm if norm is not None else ""
    if len(self._orig_buf) + len(orig) + 1 <= self._max_chunk:
        self._append_to_buffer(orig, norm_str)
    elif len(self._orig_buf) >= self._min_chunk:
        self._emit_and_start_new(result, orig, norm_str)
    else:
        # retain short (< min_chunk) buffer
        result.append((self._orig_buf, self._norm_buf or None))
        self._orig_buf = orig
        self._norm_buf = norm_str
```
When the first sentence is oversized and `min_chunk > 0`, the first two branches are skipped and the `else` appends `("", None)` (empty buffer) before setting the buffer to the oversized sentence. The oversized sentence then flows into the next iteration's `_emit_and_start_new` and is emitted whole (exceeds `max_chunk`).

Design decisions:
- **Empty-buffer guard**: in the `else` branch, emit the buffered pair only when `self._orig_buf` is non-empty; otherwise start the new buffer from `orig` without emitting. Preserves the ragc002 retention behavior for the non-empty short-buffer case.
- **Oversized segmentation**: when `len(orig) > max_chunk`, replace the single `(orig, norm)` with the pieces from `chunk_utils._split_overlong(orig, " ", self._max_chunk)`, each seeded as its own buffer. Reuses the shared rule so the JA and English/heading paths cannot drift.
- **Normalization of split parts**: set `normalized_content = None` for split sub-parts (UNK-02); COALESCE falls back to the original text. This keeps REQ-004 intact.
- `_split_overlong` raises `ValueError` on `max_chunk <= 0`; config validation (out of scope) is the guard, consistent with the English path.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Regression test (red)**
   - [ ] Add a test to `tests/rag/ingestion/test_chunk_splitter.py` asserting a single oversized first sentence (`len > max_chunk`) yields no empty pair and no oversized pair (REQ-001, REQ-002, REQ-005).
   - [ ] Confirm current test fails (empty pair present) before the fix.
2. **Phase 2: Empty-buffer emission guard**
   - [ ] In `scripts/rag/ingestion/chunk_japanese.py`, emit the buffered pair in the `else` branch only when `self._orig_buf` is non-empty; otherwise start the new buffer from `orig` (REQ-001, REQ-005).
   - [ ] Confirm `TestJapaneseMergeRetention.test_short_lead_before_oversized_is_retained` still passes (REQ-006).
3. **Phase 3: Oversized sentence segmentation**
   - [ ] Segment an input sentence longer than `max_chunk` via `chunk_utils._split_overlong` and seed each piece as its own buffer in `_merge_ja_sentence_pairs` (REQ-002).
   - [ ] Set `normalized_content = None` for split sub-parts (REQ-004, UNK-02).
   - [ ] Add parameterized oversized-first-sentence cases (REQ-005).
4. **Phase 4: Documentation**
   - [ ] Document the JA oversized-sentence rule and non-empty-content guarantee in `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (REQ-007).
5. **Phase 5: Deployment & Verification**
   - [ ] Run the chunk test suite and confirm all stay green (REQ-006, REQ-005).
   - [ ] Optional integration smoke: `process_file` + `group` + `route` for an oversized-first JA document; assert no `failed/` entry and a consumable sentinel (REQ-003).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Unit + integration | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | All chunk tests green; new regression test passes |
| `scripts/rag/ingestion/chunk_japanese.py` | Lint/format | `uv run ruff format --check` && `uv run ruff check` | Clean |
| `tests/rag/ingestion/test_chunk_splitter.py` | Lint/format | `uv run ruff format --check` && `uv run ruff check` | Clean |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Doc quality | `uv run python tools/check_docs_quality.py` | No findings |

## Risks
- **Risk**: Changing the `else` branch could drop a short lead sentence that precedes an oversized next sentence, regressing ragc002. → **Mitigation**: Guard only the empty-buffer case (`if self._orig_buf`); keep the existing retention path for non-empty buffers; `TestJapaneseMergeRetention` asserts no source text is dropped.
- **Risk**: Character-level splitting may produce awkward Japanese sub-chunks. → **Mitigation**: Acceptable per shared-helper contract; recorded as UNK-02 for owner decision; COALESCE preserves original text.
- **Risk**: Overlap with sibling merger-unification issue on `scripts/rag/ingestion/chunk_japanese.py`. → **Mitigation**: Land this bugfix first; record any overlap judgment in `Assumptions`; `check_plan_target_overlaps.py` run at freeze.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Regression test (red) | Pending | — | — | `tests/rag/ingestion/test_chunk_splitter.py` |
| 2 | Phase 2: Empty-buffer emission guard | Pending | — | — | `scripts/rag/ingestion/chunk_japanese.py` |
| 3 | Phase 3: Oversized sentence segmentation | Pending | — | — | `scripts/rag/ingestion/chunk_japanese.py`, `scripts/rag/ingestion/chunk_utils.py` |
| 4 | Phase 4: Documentation | Pending | — | — | `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` |
| 5 | Phase 5: Deployment & Verification | Pending | — | — | all target files |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-113354
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
