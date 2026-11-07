## Goal

Prevent `_merge_ja_sentence_pairs` from silently dropping a short sentence (`< min_chunk`)
that precedes an oversized next sentence, so no source Japanese text is lost on ingestion.
Align the Japanese path with the documented English "merge, do not discard" contract
(REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The retained sub-`min_chunk` chunk is accepted by the downstream pipeline (embedding/
  index); data retention is preferable to loss (Plan Assumption, UNK-02). If the pipeline
  rejects sub-`min_chunk` chunks, switch to the prepend alternative described below.
- Emitting the short sentence as its own chunk is the simplest deterministic option (Plan
  Design, Alternative A); prepend-to-next is the fallback if UNK-02 holds.
- The `None`-normalized COALESCE fallback must be preserved: an empty normalized form is
  surfaced as `None` so downstream COALESCE falls back to the original text (matches the
  method docstring).
- `test_chunk_splitter.py` is also targeted by sibling plan
  `plans/done/20261107-084815_ragc001_code-chunk-size.md`; both add distinct,
  non-contradictory tests (this one: Japanese retention; ragc001: code-size bound).
  Compatible (`check_plan_target_overlaps.py`). Add this test in an isolated class/method
  so it never collides with ragc001's additions.

## Design decisions

- Replace the `else` branch (lines 93-94) with a **retain** branch that emits the short
  `< min_chunk` buffer as its own chunk pair, then starts a fresh buffer from the current
  sentence, instead of `_reset_buffer` discarding it (Plan Design, Alternative A —
  recommended: simplest and fully deterministic, preserves all original text).

## Alternatives considered

- **Prepend to next chunk**: carry the short buffer onto the front of the oversized
  sentence's chunk. Also retains data and keeps every chunk `>= min_chunk` except possibly
  the very first. Rejected as primary because it is more invasive (must splice into the
  just-started buffer) and the plan recommends the simpler emit-alone unless UNK-02
  indicates the pipeline rejects sub-`min_chunk` chunks.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_japanese.py`
### Procedure

- In `_merge_ja_sentence_pairs` (chunk_japanese.py, lines 93-94), replace
  `self._reset_buffer(orig, norm_str)` so a short (`< min_chunk`) buffer that cannot join
  an oversized next sentence is retained: append the current buffer as its own chunk pair,
  then start a fresh buffer from the current sentence:
  ```python
  else:
      # Retain the short (< min_chunk) buffer instead of dropping it: emit it
      # as its own chunk, then start a fresh buffer from this sentence.
      result.append((self._orig_buf, self._norm_buf or None))
      self._orig_buf = orig
      self._norm_buf = norm_str
  ```
  (REQ-001, REQ-002). This preserves all original text and the `None` COALESCE fallback.
- Do NOT change the English `merge_text_items` algorithm, the text chunkers' `max_chunk`
  behavior, the normal append branch (lines 89-90), the `_emit_and_start_new` branch
  (lines 91-92), or the post-loop tail handling (lines 95-101).

### Method

- The three-way branch at lines 89-94 is: fits → `_append_to_buffer`; buffer already
  `>= min_chunk` → `_emit_and_start_new`; **else** (buffer `< min_chunk` and item does not
  fit) → currently `_reset_buffer` (discard). The retain branch only fires in the third
  case, so the normal-sized-item paths are untouched (REQ-003).
- Appending `(self._orig_buf, self._norm_buf or None)` mirrors the tail-append at lines
  98-99, preserving the `None`-COALESCE contract.
- Starting `self._orig_buf = orig / self._norm_buf = norm_str` (without overlap) keeps this
  edge case deterministic; the oversized sentence that triggered the branch is over budget,
  so carrying overlap from the tiny buffer adds no meaningful context. The post-loop tail
  handling (lines 95-101) then sees the oversized sentence as the buffer and appends it
  normally (it is `>= min_chunk`), so it is not double-emitted.

### Details

- Reproduced-case trace (min=40, max=500): the 30-char lead pairs into the buffer
  (30+1 ≤ 500); the 480-char sentence does not fit (30+480+1 = 511 > 500) and the buffer
  (30) is `< min_chunk` (40), so the retain branch fires — the 30-char lead is emitted as
  its own chunk and the 480-char sentence starts a fresh buffer that is appended at loop
  end. Both sentences appear in output (REQ-002).
- The retain branch changes nothing for the common case where the buffer is already
  `>= min_chunk` (that path still goes through `_emit_and_start_new` with overlap intact).

### Companion test files
- `tests/rag/ingestion/test_chunk_splitter.py`
  - Procedure: add `test_short_lead_before_oversized_is_retained (new)` to a new
    `class TestJapaneseMergeRetention (new)`: build a splitter via `_make_splitter()`, set
    `_min_chunk = 40`, `_max_chunk = 500`, `_chunk_overlap = 50`, feed
    `[(lead_30, None), (sentence_480, None)]` to
    `splitter._merge_ja_sentence_pairs(...)` and assert both the 30-char lead and the
    480-char sentence appear in the returned original texts (REQ-001, REQ-002).
  - Validation: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -k
    TestJapaneseMergeRetention -v` — fails before this procedure (RED) and passes after;
    then `uv run pytest tests/rag/ingestion`.

## Compatibility considerations

- Blast radius is scoped to the Japanese text path: `_merge_ja_sentence_pairs` is called
  only by `_chunk_japanese` (chunk_splitter.py); the English path uses
  `_merge_paragraphs_en` and the code path uses `merge_text_items`, neither of which is
  touched (REQ-003).
- The retained chunk may fall below `min_chunk`; downstream `embed_and_store`/index accept
  smaller chunks, and no source text is dropped. If the pipeline rejects sub-`min_chunk`
  chunks, switch to the prepend alternative (Plan UNK-02).

## Security considerations

N/A: no new input parsing, privilege, or data-handling path; string accumulation.

## Rollback considerations

N/A: revert the single commit.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Unit: short lead retained before oversized sentence | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -k TestJapaneseMergeRetention -v` | green; lead present in output |
| Regression | `uv run pytest tests/rag/ingestion` | no new failures; existing JA/EN cases unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | clean, no new findings |

## Completion criteria

- AC-1: `_merge_ja_sentence_pairs` never drops a non-empty original sentence; every input
  original appears in at least one emitted chunk (REQ-001).
- AC-2: the reproduced short-lead + oversized-sentence case (min=40, max=500) keeps the
  30-char lead in output (REQ-002).
- AC-3: existing Japanese/English splitter tests pass unchanged; `chunk_overlap` and
  `None` COALESCE fallback preserved (REQ-003).

## Out of Scope

- Changing the English `merge_text_items` algorithm or its tail-merge behavior (ragc001,
  sibling plan).
- Changing `min_chunk`/`max_chunk`/`chunk_overlap` values (tracked separately, `nc034`).
- The code-chunk size bound (ragc001, sibling plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261107-113000 | 20261107-113506 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261107-113000 | 20261107-113506 | Companion `tests/rag/ingestion/test_chunk_splitter.py` added in same change set Companion test TestJapaneseMergeRetention::test_short_lead_before_oversized_is_retained added to tests/rag/ingestion/test_chunk_splitter.py; RED->GREEN. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261107-113010 | 20261107-114801 | Includes diff-cover ≥ 90% Full suite 11901 passed / 11 skipped; diff-cover 100% on chunk_utils.py (>=90%). chunk_japanese.py is pyproject-omitted from coverage; new retain branch directly covered by TestJapaneseMergeRetention. Static gates clean. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261107-114816 | 20261107-114816 | N/A: no docs/00_index.md task-scope mapping for scripts/rag/ingestion/chunk_japanese.py (not in the Document References by Task table); Step 6 skipped. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (no Japanese text dropped), `REQ-002` (reproduced short-lead case retained)
- **Source issue**: `issues/20261107-060510_ragc002_ja-sentence-merge-content-loss.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-084830_ragc002_ja-sentence-merge-content-loss.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-092152
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`