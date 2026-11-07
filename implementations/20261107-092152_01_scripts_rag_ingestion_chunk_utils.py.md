## Goal

Cap code chunks to the same `max_chunk` upper bound as text chunks by adding an upper
guard to the shared `merge_text_items` helper, so a single code item longer than
`max_chunk` is split at a language-independent boundary (whitespace/line or a fixed
character boundary) instead of passing through unbounded and being silently dropped by
the embedding service (REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `merge_text_items` is used only by the code path (`_chunk_code` in
  `chunk_splitter.py`); capping there does not change English (`_merge_paragraphs_en`) or
  Japanese (`_merge_ja_sentence_pairs`) text chunking (verified single production caller,
  Plan Assumption).
- Code lines contain whitespace or a fixed-character split point within `max_chunk` in the
  common case; when they do not, a hard character split at `max_chunk` is acceptable for a
  source blob (Plan Design).
- Retaining the `\n\n` separator and `chunk_overlap` semantics keeps downstream
  `read_chunk_json` artifact contract intact.
- Caveat (non-blocking, UNK-02 follow-up): the same `else` branch also drops a short lead
  item that precedes an oversized item; that is a distinct defect from the size cap and is
  out of scope for this document (size cap only). Do not attempt to fix the lead-drop here.

## Design decisions

- Add one small module-level helper `_split_overlong (new)` that splits a single over-long
  item into chunks each within `max_chunk`, instead of inlining the scan in the `else`
  branch — keeps `merge_text_items` (radon complexity B(8)) from growing and isolates the
  language-independent split for testing (Plan Design).
- Split on the first whitespace/line break within each `max_chunk` window; fall back to a
  hard character split at `max_chunk` when no whitespace exists. Never apply stopword
  removal or Sudachi morphological analysis — code stays language-independent (REQ-002).

## Alternatives considered

- Reuse the existing whitespace-aware buffer accumulation for the over-long item:
  rejected — the accumulator only merges whole items, it cannot carve a single item into
  multiple in-bounds chunks.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_utils.py`
### Procedure

- Add `_split_overlong` (new) at module level (above `merge_text_items`): given the over-long
  `item`, `sep`, and `max_chunk`, return a list of substrings each of length ≤ `max_chunk`
  whose concatenation reproduces `item`. Greedy fill: from the current start, take the
  window `item[start : start + max_chunk]`; if the window does not reach the end of `item`,
  cut at the last space or newline inside the window, otherwise hard-cut at `start +
  max_chunk`; advance `start` to the cut and repeat until the item is consumed.
- In `merge_text_items` (chunk_utils.py, lines 42-43), replace the `else: buf = item`
  branch so that a single item longer than `max_chunk` is emitted as in-bounds chunks:
  extend `result` with the chunks returned by `_split_overlong` (new) for `item`, `sep`,
  `max_chunk`, and reset `buf = ""` so the trailing `min_chunk` tail-merge logic is
  unaffected (REQ-001).
- Preserve the existing `min_chunk` tail-merge, `\n\n` separator, and `chunk_overlap`
  behavior for normal-sized items unchanged (REQ-003).

### Method

- The normal-sized path (`buf = (buf + sep + item).strip()`) and the
  `elif len(buf) >= min_chunk` branch (chunk_utils.py:37-41) are untouched; only the
  `else` branch changes.
- Split chunks are appended to `result` directly (they were contiguous in `item`), so no
  re-joining with `sep` is needed; cross-chunk `chunk_overlap` is intentionally not applied
  across split boundaries (the contract under change is the size bound, REQ-001).

### Details

- `_split_overlong` (new) operates on raw characters only (no tokenizer, no language
  model), so it is correct for any source language (REQ-002).
  it is correct for any source language (REQ-002).
- The hard-character fallback guarantees forward progress because the window width
  `max_chunk` is positive; a non-empty `item` always yields at least one chunk.
- After the split, `buf` is empty, so the post-loop tail handling
  (chunk_utils.py:44-49) returns `result` unchanged for this item.

### Companion test files
- `tests/rag/ingestion/test_chunk_utils.py`
  - Procedure: add `test_oversized_single_item_capped (new)` to `TestMergeTextItems`: call
    `merge_text_items` with a single item longer than `max_chunk` and assert every returned
    chunk is ≤ `max_chunk` and the concatenation equals the input (REQ-001).
  - Validation: `uv run pytest tests/rag/ingestion/test_chunk_utils.py -v` — fails before
    this procedure (RED) and passes after; then `uv run pytest tests/rag/ingestion`.

## Compatibility considerations

- Blast radius is scoped to the code path: `chunk_english.py` and `chunk_japanese.py`
  import only `start_next_buf`, not `merge_text_items`, so their `max_chunk` behavior is
  unchanged (REQ-003).
- Chunk counts may rise for code-heavy sources (larger code chunks are now split);
  downstream `embed_and_store`/index accept smaller chunks, and embeddings no longer drop
  the largest code chunks.

## Security considerations

N/A: no new input parsing, privilege, or data-handling path; pure string slicing.

## Rollback considerations

N/A: revert the single commit.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Unit: oversized single item capped | `uv run pytest tests/rag/ingestion/test_chunk_utils.py -v` | green; every chunk ≤ `max_chunk`; concatenation equals input |
| Regression | `uv run pytest tests/rag/ingestion` | no new failures; normal-sized item behavior unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | clean, no new findings |
| Changed lines | `uv run diff-cover coverage.xml --compare-branch=<parent> --fail-under=90` | ≥ 90% |

## Completion criteria

- AC-1: a single item longer than `max_chunk` routed through `merge_text_items` yields only
  chunks of length ≤ `max_chunk` (REQ-001).
- AC-2: splitting uses a language-independent boundary (whitespace/line or fixed
  character); no stopword removal or morphological analysis is applied (REQ-002).
- AC-3: existing normal-sized item cases in `test_chunk_utils.py` still pass unchanged
  (REQ-003).
- AC-4: the oversized-item case is covered by a green unit test; diff-cover ≥ 90%.

## Out of Scope

- Changing the English (`_chunk_english` / `_merge_paragraphs_en`) or Japanese
  (`_chunk_japanese` / `_merge_ja_sentence_pairs`) text chunking algorithm or its
  `max_chunk` behavior.
- Changing `min_chunk`/`max_chunk`/`chunk_overlap` values (tracked separately, `nc034`).
- The short-lead-drop defect of the same `else` branch (distinct from the size cap).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/rag/ingestion/test_chunk_utils.py` added in same change set |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes diff-cover ≥ 90% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (code chunk size bound), `REQ-002` (language-independent split)
- **Source issue**: `issues/20261107-055949_ragc001_code-chunk-size.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-084815_ragc001_code-chunk-size.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-092152
- **Related target files**: `scripts/rag/ingestion/chunk_utils.py`, `tests/rag/ingestion/test_chunk_utils.py`
