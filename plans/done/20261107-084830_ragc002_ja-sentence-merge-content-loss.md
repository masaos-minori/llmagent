# Plan Output Template (Canonical)

## Goal
- Make `ChunkJapaneseMixin._merge_ja_sentence_pairs` retain a short sentence (< `min_chunk`)
  that precedes an oversized sentence instead of dropping it, so no source Japanese text
  is silently lost on ingestion. Align the Japanese path with the English contract
  ("merge, do not discard").

## Priority
Medium

## Scope
- **In-Scope**:
  - Replace the buffer-reset branch of `_merge_ja_sentence_pairs`
    (`scripts/rag/ingestion/chunk_japanese.py`, line 93-94) so a short sentence that
    cannot join an oversized next sentence is retained — emitted as its own chunk (even if
    below `min_chunk`) or prepended to the next chunk — and never dropped.
  - Add a unit test asserting a short sentence (< `min_chunk`) preceding an oversized
    sentence is retained, not dropped.
  - Add a regression test covering the exact reproduced case (30-char lead + 480-char
    sentence over budget, `min_chunk=40`, `max_chunk=500`).
- **Out-of-Scope**:
  - Changing the English `merge_text_items` algorithm or its tail-merge behavior.
  - Changing `min_chunk`/`max_chunk`/`chunk_overlap` values (tracked separately, see `nc034`).
  - The code-chunk size bound (tracked separately, see `ragc001`).
- **Dependencies**:
  - **Depends on**: `issues/done/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md` | phase all | same unvalidated sizing area; the retention fix is correct regardless of the specific bounds. Record as non-blocking.

## Background
`ChunkSplitter` composes `ChunkEnglishMixin` and `ChunkJapaneseMixin` via multiple
inheritance. Both text paths accumulate sentences into buffers bounded by
`min_chunk`/`max_chunk` (`config/chunk_splitter.toml`: `min_chunk=40`, `max_chunk=500`,
`chunk_overlap=50`). The English accumulator lives in
`scripts/rag/ingestion/chunk_utils.py::merge_text_items`; the Japanese accumulator lives in
`scripts/rag/ingestion/chunk_japanese.py::_merge_ja_sentence_pairs`. Both sit in the same
unvalidated sizing area flagged by
`issues/done/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md`.

## Problem
`_merge_ja_sentence_pairs` branches on each `(orig, norm)` pair: if the pair fits it
appends; else if the buffer is `>= min_chunk` it emits and starts a new buffer; **else it
resets the buffer to `orig`** (`_reset_buffer`, line 93-94), discarding whatever was
already accumulated. When the running buffer holds a short sentence shorter than
`min_chunk` and the next sentence does not fit, the third branch fires and the accumulated
short sentence is dropped, never emitted.

Reproduced at HEAD with config bounds (min=40, max=500): a 30-char lead sentence followed
by a 480-char sentence yields one 480-char chunk; the 30-char lead is absent from the
output.

Note: the Issue describes the English path as "never drops", but the English *text* path
uses its own `_merge_paragraphs_en` (not `merge_text_items`), which flushes-and-merges
rather than resets. The helper named in the Issue (`merge_text_items`) is actually the
*code*-path helper and shares this same drop defect — that instance is handled by sibling
issue `ragc001`. This Issue scopes the fix to the Japanese text path only.

## Reason for Change
Ingestion must not silently drop source text. For Japanese corpora, any document containing
a short clause before a long one is at risk, and the loss is silent (the run reports
success and the total chunk count). The fix aligns the Japanese path with the documented
English contract ("merge, do not discard") and removes an untested assumption that every
accumulated sentence is retained.

## Implementation Intent
In `_merge_ja_sentence_pairs`, replace the buffer-reset branch so a short sentence that
cannot join the oversized next sentence is retained rather than dropped. Prefer emitting
the short sentence as its own chunk (even if below `min_chunk`) or appending it to the
next chunk's front, whichever keeps behavior deterministic and preserves all original
text. Do NOT change the English `merge_text_items` algorithm or the text chunkers'
`max_chunk` behavior. Preserve overlap handling and the `None`-normalized COALESCE
semantics.

## Requirements
- `REQ-001`: Every non-empty original sentence in a Japanese document appears in at least
  one emitted chunk; `_merge_ja_sentence_pairs` never drops source text.
- `REQ-002`: The reproduced short-lead + oversized-sentence case retains the lead sentence
  in output.
- `REQ-003`: Existing Japanese/English splitter tests pass unchanged; `chunk_overlap` and
  `None` normalized-form COALESCE fallback are preserved.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | `_merge_ja_sentence_pairs` line 93-94 `else: self._reset_buffer(orig, norm_str)` discards a short (< `min_chunk`) buffer when the next sentence does not fit; replace with a retain branch (emit alone or prepend) | REQ-001, REQ-002 | `_reset_buffer` (line 128-131) sets `self._orig_buf = orig`, dropping accumulated text; reproduced 30+480 case yields `[480]` with lead missing (Step 2) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Add | Unit + regression test asserting a short sentence (< `min_chunk`) preceding an oversized sentence is retained | REQ-001, REQ-002 | No existing test pins the mid-loop drop; `TestJapaneseMergeRegression` covers only end-of-stream tail merge and direct helper calls (Step 3) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |

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
| `scripts/rag/ingestion/chunk_utils.py` | Read `merge_text_items` to mirror its "merge short tail, never drop" contract and preserve `None` COALESCE semantics consistently | `scripts/rag/ingestion/chunk_japanese.py` (REQ-003) |
| `scripts/rag/ingestion/chunk_english.py` | Confirm the English text path retains content via `_flush_and_merge`/`_flush_and_split` (reference for the intended retention semantics) | `scripts/rag/ingestion/chunk_japanese.py` (REQ-003) |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Verify whether the merge policy table distinguishes English vs Japanese; update only if it documents the drop behavior being removed | `scripts/rag/ingestion/chunk_japanese.py` (REQ-001) |

## Acceptance Criteria
- No original Japanese sentence is dropped by `_merge_ja_sentence_pairs` (`REQ-001`).
- The reproduced short-lead + oversized-sentence case retains the lead sentence in output (`REQ-002`).
- Existing Japanese/English splitter tests pass unchanged (`REQ-003`).

## Tests
- Unit: `_merge_ja_sentence_pairs` with a short lead before an oversized sentence retains the lead (`tests/rag/ingestion/test_chunk_splitter.py`, `REQ-001`).
- Regression: the exact reproduced case (min=40, max=500) keeps the 30-char lead (`REQ-002`).
- Run `uv run pytest tests/rag/ingestion` and confirm no regression (`REQ-003`).

## Documentation Impact
`N/A: no doc change required unless the merge policy table in
`rag_02_03_ingestion_pipeline-chunksplitter.md` currently documents that the Japanese path
drops short sentences`. If so, note that the Japanese path retains short sentences (never
drops them), matching the English contract (intent and boundary only; no
implementation-derived detail per `skills/DESIGN.md` docs policy). The plan reads the doc
to verify current state.

## Assumptions
- Retained sub-`min_chunk` chunks are accepted by the downstream pipeline (embedding/index);
  data retention is preferable to loss (per Issue constraint).
- Emitting the short sentence as its own chunk is the simplest deterministic option;
  prepending to the next chunk is the alternative if sub-`min_chunk` chunks are undesirable.
- The `None`-normalized COALESCE fallback must be preserved for the retained chunk's
  normalized form.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner preference: emit the short sentence as its own sub-`min_chunk` chunk, or prepend it to the next chunk? Both retain data; prefer the simpler deterministic option. | Owner decision | Emit-alone is recommended (see Implementation Intent); record choice in the implementation procedure | False |
| UNK-02 | Does retaining sub-`min_chunk` chunks change downstream embedding/index expectations? | Pipeline acceptance tests / index contract | Confirm the pipeline accepts small chunks during implementation; if not, prefer prepend | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Modify | Low — private mixin method `_merge_ja_sentence_pairs`; called only within the Japanese text path; complexity B(10) is the highest in the file | 2 commits | Low — single author (`sugimoma-c`) | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Add | Low — test-only addition; higher churn (6 commits/30d) than the source under change | 6 commits | N/A | not applicable (rsynced) |

## Design
Path A: target is a private mixin method (`_merge_ja_sentence_pairs`), ≤3 files, no
public/runtime interface change. Architecture/dependency/historical analysis is not
required; blast radius judged qualitatively from direct verification (Step 3).

**Design decision — emit-alone vs. prepend (open in the Issue).**
- **Alternative A (recommended): emit the short sentence as its own chunk**, even though
  it falls below `min_chunk`. Simplest and fully deterministic; preserves all original
  text.
- **Alternative B: prepend** the short sentence to the next chunk's front. Also retains
  data; keeps every chunk `>= min_chunk` except possibly the very first.
- **Choice**: prefer A unless UNK-02 indicates the pipeline rejects sub-`min_chunk`
  chunks.

## Implementation steps
1. **Phase 1: Retain the short buffer in `_merge_ja_sentence_pairs`**
   - [ ] Replace the `else` branch (line 93-94) so a short (< `min_chunk`) buffer that
     cannot join an oversized next sentence is retained: emit it as its own chunk (or
     prepend it to the next chunk), never dropped. Preserve `chunk_overlap` and the
     `None` COALESCE fallback (`chunk_japanese.py`, `REQ-001`, `REQ-002`).
2. **Phase 2: Tests**
   - [ ] Add a unit test asserting a short sentence (< `min_chunk`) before an oversized
     sentence is retained (`REQ-001`).
   - [ ] Add a regression test for the exact reproduced case (30-char lead + 480-char
     sentence, min=40, max=500) keeping the lead (`REQ-002`).
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
     scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`,
     `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run pytest tests/rag/ingestion`,
     and `uv run diff-cover coverage.xml --compare-branch=<parent> --fail-under=90`; confirm
     no regression and ≥90% diff coverage (`REQ-003`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py::_merge_ja_sentence_pairs` | Unit: short lead retained before oversized sentence | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` | green; lead present in output |
| Full ingestion suite | Regression | `uv run pytest tests/rag/ingestion` | no new failures |
| Changed lines | Diff coverage | `uv run diff-cover coverage.xml --compare-branch=<parent> --fail-under=90` | ≥90% |

## Risks
- **Risk**: Emitting a sub-`min_chunk` chunk may surprise downstream consumers that assume
  a minimum chunk size. → **Mitigation**: record UNK-01/UNK-02 in the implementation
  procedure; prefer prepend if the pipeline rejects small chunks.
- **Risk**: The same drop defect exists in the code-path helper `merge_text_items`
  (`ragc001`) and the Issue mislabels it as the English equivalent. → **Mitigation**: this
  plan stays scoped to the Japanese text path; the code-path instance is fixed by
  `ragc001`. No scope expansion without owner approval.
- **Risk**: `test_chunk_splitter.py` has higher churn (6 commits/30d). → **Mitigation**:
  resolve merge conflicts if any at implementation time; additions are additive.

- `tests/rag/ingestion/test_chunk_splitter.py` is also targeted by sibling plan
  `plans/20261107-084815_ragc001_code-chunk-size.md`; the two add distinct,
  non-contradictory tests (Japanese retention vs code-size bound). Compatible
  (`check_plan_target_overlaps.py`).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Retain short buffer in `_merge_ja_sentence_pairs` (`chunk_japanese.py`) | In Progress | — | — |  |
| 2 | Unit + regression tests (`test_chunk_splitter.py`) | In Progress | — | — |  |
| 3 | Deployment & verification (gates + diff-cover) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| `implementations/20261107-092152_01_scripts_rag_ingestion_chunk_japanese.py.md` | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-060510_ragc002_ja-sentence-merge-content-loss.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-084815
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / AI Implementation Instruction; verified drop at HEAD | `scripts/rag/ingestion/chunk_japanese.py` | 1 | no original sentence dropped | unit retention test | Confirmed by repository evidence |
| REQ-001 | same | `tests/rag/ingestion/test_chunk_splitter.py` | 2 | retention case covered | new unit test | Confirmed by repository evidence |
| REQ-002 | Reproduced case (30+480) | `scripts/rag/ingestion/chunk_japanese.py` | 1 | lead retained in output | regression test | Confirmed by repository evidence |
| REQ-002 | same | `tests/rag/ingestion/test_chunk_splitter.py` | 2 | reproduced case kept | regression test | Confirmed by repository evidence |
| REQ-003 | Constraints (preserve overlap/COALESCE); existing tests pass | `scripts/rag/ingestion/chunk_japanese.py` | 1 | existing JA/EN tests unchanged | existing suite | Confirmed by repository evidence |
| REQ-003 | same | `tests/rag/ingestion/test_chunk_splitter.py` | 2 | existing tests pass | existing suite | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261107-092152 -->