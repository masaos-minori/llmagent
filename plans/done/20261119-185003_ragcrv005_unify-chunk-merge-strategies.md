## Goal
Extract the three divergent chunk-accumulation implementations into one collaborator that owns the min/max/overlap loop and takes the language-specific oversized-item, short-tail, and paired-companion decisions as explicit inputs, without changing any observable chunk output.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add one accumulation collaborator under `scripts/rag/ingestion/` that owns the shared min/max/overlap accumulation loop and exposes the oversized-item strategy, short-tail strategy, separator, and optional paired-companion stream as explicit inputs.
  - Route the code path (`ChunkSplitter._chunk_code` via `merge_text_items`) through the collaborator.
  - Route the English path (`ChunkEnglishMixin._merge_paragraphs_en`) through the collaborator.
  - Route the Japanese path (`ChunkJapaneseMixin._merge_ja_sentence_pairs`) through the collaborator while preserving its paired (original, normalized) companion handling.
  - Keep `start_next_buf` and `_split_overlong` as the overlap and segmentation primitives behind the collaborator.
  - Preserve the public chunk-file output format and `chunk_index` ordering exactly.
- **Out-of-Scope**:
  - Changing which text is stored for English (`issues/20261119-112014_ragcrv002_english-content-stopword-loss.md`).
  - Fixing the empty-chunk defect (`issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md`) — landed first as a deliberate behavior change, not a side effect of this extraction.
  - Removing the per-mixin buffer instance fields; that cleanup is sequenced to `issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md`.
  - Configuration validation (`issues/20261119-112015_ragcrv003_chunk-config-validation.md`).
- **Dependencies**:
  - **Depends on**: `N/A: none` — the previously required behavior fix (`issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md`) is already closed in `issues/done/`, so no open dependency gates this Plan.
  - Sequencing (non-blocking): the `ragcrv006` mixin-state-coupling work removes the per-mixin buffer fields this extraction makes unnecessary; the core extraction proceeds independently and the field removal lands with `ragcrv006`. See `Assumptions`.

## Background
- Three accumulation implementations exist under `scripts/rag/ingestion/`, each with its own oversized-item and short-tail rules:
  - `ChunkSplitter._chunk_code` → `chunk_utils.merge_text_items`: splits an overlong item with `_split_overlong`, merges a short tail into the last chunk, applies overlap via `start_next_buf`. Sole caller of `merge_text_items`.
  - `ChunkEnglishMixin._merge_paragraphs_en` (+ `_split_sentences_en`): sends an overlong paragraph to `_split_sentences_en` (which keeps an overlong sentence whole), merges a short tail with overlap via `_flush_and_merge`, and appends the final buffer unconditionally; the caller `_chunk_english` enforces `min_chunk` on the stopword-filtered length.
  - `ChunkJapaneseMixin._merge_ja_sentence_pairs`: accumulates paired (original, normalized) sentences, segments an overlong sentence with the shared `_split_overlong` rule (added by the closed `ragcrv001` fix), emits a short buffer as its own chunk, merges the tail into the last pair, and applies overlap to both the original and normalized buffers.
- Each past fix patched one copy of the rule (`issues/done/20261107-055949_ragc001_code-chunk-size.md`, `issues/done/20261107-060510_ragc002_ja-sentence-merge-content-loss.md`), so the divergence persists.
- Complexity baseline (radon): `_merge_ja_sentence_pairs` is C (16), `_merge_paragraphs_en` is B (8), `merge_text_items` is B (9). All three hold mutable buffer state on the mixin instance (`self._buf`; `self._orig_buf`/`self._norm_buf`).

## Problem
One documented rule ("min/max bound chunk size, overlap prepends the previous tail") is implemented three times with three different oversized-item, short-tail, and overlap semantics. Every future chunking change must be applied in three places, and each partial fix has left the paths diverging further.

## Reason for Change
The chunkers are the core of ingestion corpus quality and are actively tuned (last 90-day churn: `chunk_splitter.py` 14, `chunk_japanese.py` 7, `chunk_utils.py` 2, `chunk_english.py` 2). Duplicated accumulation logic is where the next divergence will appear.

## Implementation Intent
Extract one accumulation collaborator that owns min/max/overlap accumulation and takes the language-specific decisions as explicit inputs: separator, oversized-item strategy, short-tail strategy, and an optional paired-normalized companion stream. The chunkers keep their language-specific splitting and normalization and stop owning buffer state. Execute with `python-refactoring`: characterization tests pin each current behavior before extraction, and output is behavior-locked before and after.

## Requirements
- `REQ-001`: One collaborator under `scripts/rag/ingestion/` owns the shared accumulation loop and exposes oversized-item, short-tail, separator, and optional paired-companion inputs.
- `REQ-002`: The code path routes through the collaborator; `merge_text_items` remains the code path's entry point (delegating to the collaborator) so `_chunk_code`'s call site is unchanged.
- `REQ-003`: The English path routes through the collaborator; its paragraph/sentence splitting and stopword-filtered `min_chunk` enforcement stay in the mixin.
- `REQ-004`: The Japanese path routes through the collaborator with the paired (original, normalized) companion stream preserved as part of the collaborator contract.
- `REQ-005`: Behavior is locked — characterization tests pin each path's exact current output and pass unchanged after extraction; no behavior revealed as a defect is silently fixed.
- `REQ-006`: The public chunk-file output format and `chunk_index` ordering are unchanged.
- `REQ-007`: The utility-functions documentation is updated to describe the collaborator's ownership and strategy inputs.

## Implementation Target Files
**Freeze status**: Frozen (Step 8: all six rows `Verified`, `audit_plan_target_paths.py` reports 0 findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` | Modify | Add the single accumulation collaborator; keep `start_next_buf` and `_split_overlong` as primitives; make `merge_text_items` a thin delegating wrapper for the code path | REQ-001, REQ-002, REQ-006 | Three divergent loops confirmed in Steps 2–3; radon B(9)/A(5)/A(3); sole caller `_chunk_code` in Step 3 | `test_chunk_utils.py` | Verified |
| `scripts/rag/ingestion/chunk_english.py` | Modify | Route `_merge_paragraphs_en` through the collaborator; drop the mixin's own accumulation loop and overlap handling; keep sentence splitting and filter-driven `min_chunk` | REQ-003, REQ-005, REQ-006 | `_merge_paragraphs_en` B(8) holds `self._buf`; caller `_chunk_english` filters by min length in Step 2 | `test_chunk_splitter.py` | Verified |
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | Route `_merge_ja_sentence_pairs` through the collaborator preserving the paired (original, normalized) companion stream; keep morphological normalization | REQ-004, REQ-005, REQ-006 | `_merge_ja_sentence_pairs` C(16) holds `self._orig_buf`/`self._norm_buf`; `_split_overlong` branch from closed `ragcrv001` in Step 2 | `test_chunk_splitter.py` | Verified |
| `scripts/rag/ingestion/chunk_splitter.py` | Verify / update call site if needed | Confirm `_chunk_code` still drives the code path correctly after extraction; modify only if `merge_text_items` signature changes | REQ-002, REQ-006 | `_chunk_code` is the sole `merge_text_items` caller; `chunk_index` ordering set here in Step 3 | `test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_utils.py` | Modify | Add mutation-sensitive unit tests for the collaborator's oversized, short-tail, overlap, and paired-companion branches; host the per-path characterization fixtures | REQ-005, REQ-008 | Existing `merge_text_items` tests anchor the code path in Step 2 | `test_chunk_utils.py` | Verified |
| `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` | Modify | Document the collaborator's ownership and the strategy inputs each path supplies; coordinate with `ragcrv010` so both doc updates describe one design | REQ-007 | Doc exists under `docs/21_rag/` (index key `rag_02_07_n`); mandated by issue Documentation Impact in Step 2 | N/A | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tests/rag/ingestion/test_chunk_splitter.py` | Regression anchor: preserves current per-path output assertions that must stay green | REQ-005, REQ-006 |
| `tests/rag/ingestion/test_ingester.py` | Regression anchor for the ingestion layer around the chunkers | REQ-006 |
| `tests/rag/ingestion/test_rag_ingestion_pipeline.py` | Regression anchor for end-to-end pipeline output order | REQ-006 |
| `scripts/rag/ingestion/chunk_preparation.py` | Owns the section routing that feeds `_chunk_english`/`_chunk_japanese`/`_chunk_code`; read to preserve feeding semantics | REQ-003, REQ-004 |

## Acceptance Criteria
- Exactly one accumulation loop exists under `scripts/rag/ingestion/` (`REQ-001`; AC: code review / `test_chunk_utils.py`).
- Characterization tests pin each path's current output before the extraction and pass unchanged after it (`REQ-005`; AC: characterization tests).
- The code path's `merge_text_items` entry point is unchanged for `_chunk_code` (`REQ-002`; AC: `test_chunk_splitter.py` code-chunk cases).
- The Japanese paired (original, normalized) output is identical before and after, including `None` normalized values (`REQ-004`; AC: `test_chunk_splitter.py` Japanese cases).
- No observable behavior change: the behavior-locked comparison reports zero diffs across all three paths (`REQ-005`; AC: characterization + regression suite).
- Public chunk-file output format and `chunk_index` ordering are unchanged (`REQ-006`; AC: `test_rag_ingestion_pipeline.py`).
- The per-mixin buffer fields remain valid until removed by `ragcrv006`; this Plan introduces no dead-field usage (`REQ-003`/`REQ-004`; AC: code review).
- Documentation describes the collaborator's ownership and strategy inputs (`REQ-007`; AC: `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`).

## Tests
- Characterization: per-path fixture documents asserting the exact chunk list (and, for Japanese, the exact pair list including `None`) before the change; these must pass unchanged after extraction (`REQ-005`).
- Mutation-sensitive unit tests for the collaborator's oversized-item, short-tail (mid-stream and end-of-stream), overlap, and paired-companion branches (`REQ-001`, `REQ-008`).
- Regression: `tests/rag/ingestion/test_chunk_utils.py`, `test_chunk_splitter.py`, `test_ingester.py`, `test_rag_ingestion_pipeline.py` stay green (`REQ-005`, `REQ-006`).

## Documentation Impact
`docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` (index task "Utility functions", key `rag_02_07_n`): describe the collaborator's ownership of the accumulation loop and the strategy inputs each path supplies. Coordinate with `issues/20261119-112022_ragcrv010_chunking-docs-max-chunk.md` so the two doc updates describe one design, not two. Driven by `REQ-007`.

## Assumptions
- The three paths' observable outputs can be reproduced exactly by characterization fixtures from representative fixture documents, so behavior locking is feasible without live corpus runs.
- The oversized-item divergence (code/Japanese use `_split_overlong`; English uses sentence splitting that keeps an overlong sentence whole) is intentional per-language behavior to preserve, not a defect to unify — unless a characterization test reveals otherwise, in which case it is reported, not fixed.
- The per-mixin buffer-field removal is safely sequenced to `ragcrv006`: this Plan removes the *need* for the fields by moving accumulation into the collaborator, and `ragcrv006` performs the physical field removal. This is a sequencing dependency, not a blocking one.
- The collaborator lives inside the `rag.ingestion` layer (importlinter `rag` package boundary), so it does not alter the package's import contracts.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the three paths converge on one shared oversized-item strategy or keep per-language strategies (code/Japanese `_split_overlong` vs English sentence splitting) | Owner decision on Japanese segmentation quality and English paragraph integrity | Decided at implementation via `python-design` (Path B design decision); recorded in the implementation procedure | False |
| UNK-02 | Exact placement of the new per-path characterization fixtures (new file vs `test_chunk_utils.py`) | Convention for large characterization fixtures | Decide in implementation; keep under `tests/rag/ingestion/` | False |
| UNK-03 | Per-mixin buffer-field removal is sequenced to `issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md`; this Plan removes the need but defers the physical field removal | Owner decision on field-removal ordering | `ragcrv006` lands, then remove the now-dead mixin buffer fields | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` | Modify | callers of the three chunkers | 2 (90d) | N/A: tool unavailable (single-owner layer) | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_english.py` | Modify | `ChunkSplitter` English path | 2 (90d) | N/A: tool unavailable | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | `ChunkSplitter` Japanese path | 7 (90d) | N/A: tool unavailable | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | ingestion routing / `chunk_index` | 14 (90d) | N/A: tool unavailable | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_utils.py` | Modify | test suite | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` | Modify | readers of the ingestion utils doc | N/A | N/A | not applicable (rsynced) |

## Design
This is a behavior-preserving refactoring (Path B: six target files, a new collaborator boundary, and a public-output contract at stake). Execute under `python-refactoring`: characterization tests first, behavior locked before and after, no intended behavior change except the separately filed fixes.

### Evidence: the three accumulation rules diverge
The three implementations encode the same min/max/overlap intent differently. This table is the baseline the extraction must preserve (each column is a behavior the collaborator must reproduce via an explicit input, not erase):

| Behavior | code (`merge_text_items`) | English (`_merge_paragraphs_en`) | Japanese (`_merge_ja_sentence_pairs`) |
|---|---|---|---|
| Oversized item | `_split_overlong` | `_split_sentences_en` (keeps overlong sentence whole) | `_split_overlong` |
| Short tail, mid-stream (buffer below `min_chunk`) | grow buffer (`buf = item`) | grow buffer (`self._buf = para`) | emit buffer as own chunk, then fresh buffer |
| Short tail, end of stream | merge into last chunk | append unconditionally (caller enforces `min_chunk` on filtered length) | merge tail into last pair (both buffers) |
| Overlap applied to | single buffer | single buffer | both original and normalized buffers |
| `min_chunk` check at end | yes | none (always appended) | yes |
| Paired companion stream | none | none | paired (original, normalized) |

### Collaborator contract (proposed)
One accumulator taking explicit strategy inputs rather than encoding one language's choices:
- Inputs: ordered items, separator, `min_chunk`, `max_chunk`, `chunk_overlap`, an oversized-item strategy selector, a short-tail strategy selector, and an optional companion-stream handler (Japanese) or none (code/English).
- The oversized-item strategy and short-tail strategy are the two open design axes (UNK-01). Two viable options: (a) one shared strategy across all paths, or (b) per-language strategy values passed in. Preserve current behavior for each path regardless of which option is chosen; the choice affects maintainability, not output.
- The paired-companion handling is modeled as a first-class collaborator input (a per-item companion value plus a merge/overlap function) instead of a parallel buffer, satisfying the issue's "part of the accumulator contract instead of a parallel buffer."

### Public-contract constraint
The chunk-file output format and `chunk_index` ordering are external contracts. The extraction must produce byte-identical chunk lists (and pair lists for Japanese) so downstream serialization and ordering are unaffected (`REQ-006`).

### importlinter
The `rag` package forbids importing `agent`/`mcp_servers`; the collaborator stays within `rag.ingestion` and only depends on `start_next_buf`/`_split_overlong`, so no package-boundary contract changes.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Characterization (behavior lock)**
   - [ ] Add per-path characterization fixtures asserting the exact current chunk list (and pair list for Japanese) for representative inputs on `tests/rag/ingestion/test_chunk_utils.py` (`REQ-005`).
   - [ ] Run the fixtures to capture the pre-change baseline as the golden reference (`REQ-005`).
2. **Phase 2: Extract the collaborator**
   - [ ] Add the single accumulation collaborator to `scripts/rag/ingestion/chunk_utils.py` with explicit oversized-item, short-tail, separator, and optional companion inputs; keep `start_next_buf` and `_split_overlong` as primitives (`REQ-001`).
   - [ ] Add mutation-sensitive unit tests for the collaborator's oversized, short-tail, overlap, and companion branches (`REQ-001`, `REQ-008`).
3. **Phase 3: Route the code path**
   - [ ] Make `merge_text_items` delegate to the collaborator so `_chunk_code`'s call site is unchanged; verify `test_chunk_splitter.py` code cases (`REQ-002`, `REQ-006`).
4. **Phase 4: Route the English path**
   - [ ] Replace `_merge_paragraphs_en`'s loop with the collaborator, preserving sentence splitting and filter-driven `min_chunk`; keep `_chunk_english`'s stopword filtering (`REQ-003`, `REQ-005`).
5. **Phase 5: Route the Japanese path**
   - [ ] Replace `_merge_ja_sentence_pairs`'s loop with the collaborator, modeling the paired (original, normalized) stream as a collaborator input; keep morphological normalization (`REQ-004`, `REQ-005`).
6. **Phase 6: Verify behavior lock and document**
   - [ ] Re-run characterization + full regression suite; assert zero diffs from the Phase 1 baseline (`REQ-005`, `REQ-006`).
   - [ ] Update the utility-functions documentation to describe the collaborator and strategy inputs (`REQ-007`).
   - [ ] Hand off `ragcrv006` for per-mixin buffer-field removal now that the need is gone.

### Release units
N/A: no release unit — each phase lands in a testable state (characterization green before extraction, per-path regression green after each route).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Collaborator (`chunk_utils.py`) | Unit: oversized, short-tail, overlap, companion branches; mutation testing | `uv run pytest tests/rag/ingestion/test_chunk_utils.py` | All branch tests pass; mutations caught |
| Code path (`chunk_splitter.py`) | Regression: code-chunk output | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | Zero diff from baseline |
| English path (`chunk_english.py`) | Regression: English chunk output | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | Zero diff from baseline |
| Japanese path (`chunk_japanese.py`) | Regression: Japanese pair output incl. `None` | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | Zero diff from baseline |
| End-to-end | Regression: pipeline output order/format | `uv run pytest tests/rag/ingestion/test_ingester.py tests/rag/ingestion/test_rag_ingestion_pipeline.py` | Green; `chunk_index` ordering preserved |

## Risks
- **Risk**: The three paths' divergent semantics make a single collaborator over-generalized, risking a subtle behavior change. → **Mitigation**: behavior locking via characterization tests (Phase 1) plus a pre/post diff gate (Phase 6); any revealed defect is reported, not silently fixed.
- **Risk**: The Japanese paired-companion stream is easy to mishandle (original vs normalized overlap applied inconsistently). → **Mitigation**: model the companion as an explicit collaborator input with dedicated mutation tests; Japanese regression cases assert `None` normalized values.
- **Risk**: Removing or reordering accumulation breaks the public `chunk_index` ordering contract. → **Mitigation**: `test_rag_ingestion_pipeline.py` regression gate; output format asserted unchanged (`REQ-006`).
- **Risk**: Buffer-field removal collides with `ragcrv006`. → **Mitigation**: defer field removal to `ragcrv006`; this Plan introduces no dead-field usage and names `ragcrv006` as a sequencing dependency.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`. Default rows for a freshly generated Plan (replace with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Characterization / behavior lock | In Progress | — | — |  |
| 2 | Phase 2: Extract the accumulation collaborator | In Progress | — | — |  |
| 3 | Phase 3: Route the code path | In Progress | — | — |  |
| 4 | Phase 4: Route the English path | In Progress | — | — |  |
| 5 | Phase 5: Route the Japanese path | In Progress | — | — |  |
| 6 | Phase 6: Verify behavior lock and document | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261119-194357_01_scripts_rag_ingestion_chunk_utils_py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261119-194357_02_scripts_rag_ingestion_chunk_english_py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261119-194357_03_scripts_rag_ingestion_chunk_japanese_py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261119-194357_04_scripts_rag_ingestion_chunk_splitter_py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261119-194357_05_tests_rag_ingestion_test_chunk_utils_py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261119-194357_06_docs_21_rag_rag_02_07_ingestion_pipeline_utils_md.md` | 6 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-185003
- **Related target files**: `scripts/rag/ingestion/chunk_utils.py`, `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_japanese.py`, `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_utils.py`, `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary / Required Changes / Acceptance Criteria (`one accumulation loop`) | `scripts/rag/ingestion/chunk_utils.py` | Step 2 | Exactly one accumulation loop | `test_chunk_utils.py` unit + mutation tests | Confirmed by repository evidence |
| REQ-002 | Required Changes (route code path) | `scripts/rag/ingestion/chunk_utils.py`, `scripts/rag/ingestion/chunk_splitter.py` | Step 3 | `merge_text_items` entry unchanged | `test_chunk_splitter.py` code cases | Confirmed by repository evidence |
| REQ-003 | Required Changes (route English path) | `scripts/rag/ingestion/chunk_english.py` | Step 4 | English output unchanged | `test_chunk_splitter.py` English cases | Confirmed by repository evidence |
| REQ-004 | Required Changes (paired companion) | `scripts/rag/ingestion/chunk_japanese.py` | Step 5 | Japanese pairs incl. `None` unchanged | `test_chunk_splitter.py` Japanese cases | Confirmed by repository evidence |
| REQ-005 | Constraints / AI Implementation Instruction / Testing Expectations | `tests/rag/ingestion/test_chunk_utils.py` | Steps 1, 6 | Behavior locked (zero diff) | characterization + regression suite | Confirmed by repository evidence |
| REQ-006 | Constraints (public format / `chunk_index`) | `scripts/rag/ingestion/chunk_splitter.py` | Steps 3–6 | Output format/order unchanged | `test_rag_ingestion_pipeline.py` | Confirmed by repository evidence |
| REQ-007 | Documentation Impact | `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` | Step 6 | Collaborator documented | doc review | Needs confirmation |