## Goal

Add a `ChunkSplitter`-level test asserting that a long single-line code block routed
through `_chunk_code` / `merge_text_items` yields only chunks within `max_chunk`
(REQ-001). This pins the upper-guard fix added to `merge_text_items` by sibling procedure
`20261107-092152_01_scripts_rag_ingestion_chunk_utils.py.md`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `test_chunk_splitter.py` is also targeted by sibling plan
  `plans/20261107-084830_ragc002_ja-sentence-merge-content-loss.md`; both add distinct,
  non-contradictory tests (this one: code-size bound; ragc002: Japanese retention). The
  two are compatible (`check_plan_target_overlaps.py`) — add this test in an isolated
  class/method so it never collides with ragc002's additions.
- `_chunk_code` (chunk_splitter.py, lines 218-228) splits the block at blank lines and
  calls the shared `merge_text_items` with the real `self._min_chunk` / `self._max_chunk`
  / `self._chunk_overlap`, so a single over-long block reaches `merge_text_items` as one
  item (verified at HEAD).
- This is an additive test-only change; existing cases in `test_chunk_splitter.py` stay
  unchanged (REQ-003).

## Design decisions

- Put the new assertion in its own `class TestCodeChunkSizeBound (new)` rather than
  extending an existing class, so the size-bound check is isolated from the IO /
  end-to-end tests and from ragc002's Japanese-retention test.

## Alternatives considered

- Add the assertion to the existing `TestFetchedAtPropagation` class: rejected — that
  class asserts `fetched_at` propagation, not chunk size, and mixing concerns reduces
  signal (and risks overlap with ragc002's additions there).

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`
### Procedure

- Add `class TestCodeChunkSizeBound (new)` immediately after `class TestIsMarkdownSource`
  in `test_chunk_splitter.py`.
- Inside it, add `test_long_single_line_code_block_capped_to_max_chunk (new)`: build a
  splitter via `_make_splitter()`, set `_min_chunk = 40`, `_max_chunk = 500`,
  `_chunk_overlap = 50`, pass a single line of `"x" * 1200` (no blank lines, longer than
  `max_chunk`) to `splitter._chunk_code(...)`, and assert the result has at least two
  chunks, every chunk is ≤ `max_chunk`, and the concatenation of the chunks equals the
  input (REQ-001).
- Do not touch any existing class, helper, or import.

### Method

- `_chunk_code` reads only `self._min_chunk` / `self._max_chunk` / `self._chunk_overlap`,
  so setting those three attributes on the `_make_splitter()` instance (which uses
  `object.__new__`) is sufficient to drive the real code path without constructing the
  full config-backed splitter.
- A single line with no blank lines means `re.split(r"\n{2,}", code.strip())` yields one
  block, which `merge_text_items` receives as a single item longer than `max_chunk` — the
  exact case the upper guard in procedure `.../chunk_utils.py` fixes.

### Details

- The round-trip assertion (`"".join(chunks) == input`) guards against a split that drops
  or duplicates characters; it is stronger than REQ-001 requires but cheap and pins the
  "concatenation reproduces the item" behavior of the split helper.
- `max_chunk` is read from the attributes set on the splitter, not a magic number, so the
  assertion tracks the configured bound.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New size-bound test | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -k TestCodeChunkSizeBound -v` | green; chunks ≤ `max_chunk`, ≥ 2 chunks, round-trip holds |
| Regression | `uv run pytest tests/rag/ingestion` | no new failures; existing cases unchanged |
| Static gates | `uv run ruff check scripts/ tests/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | clean, no new findings |

## Completion criteria

- AC-1: `TestCodeChunkSizeBound.test_long_single_line_code_block_capped_to_max_chunk` is
  green and asserts every `_chunk_code` output chunk is ≤ `max_chunk` (REQ-001).
- AC-2: the test fails (RED) before the `merge_text_items` upper guard lands and passes
  (GREEN) after it.
- AC-3: existing `test_chunk_splitter.py` cases still pass unchanged (REQ-003).

## Out of Scope

- Japanese sentence-merge content loss (ragc002, sibling plan).
- Changing `min_chunk` / `max_chunk` / `chunk_overlap` values (tracked separately, `nc034`).
- Any English/Japanese text-chunking behavior.

## Compatibility considerations

- Co-target: `test_chunk_splitter.py` is also modified by sibling plan
  `plans/20261107-084830_ragc002_ja-sentence-merge-content-loss.md`. Keep this change in
  its own `TestCodeChunkSizeBound` (new) class with a uniquely named test method so the two
  plans' additions remain distinct and non-contradictory (compatible per
  `check_plan_target_overlaps.py`).

## Security considerations

N/A: test-only addition; no new runtime path.

## Rollback considerations

N/A: revert the single commit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261107-112500 | 20261107-112757 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261107-112500 | 20261107-112757 | This document IS the test addition This document IS the test addition (TestCodeChunkSizeBound). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 20261107-112757 | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261107-112828 | 20261107-112828 | N/A: test-only addition; no source/docs changed. |

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
- **Requirement ID**: `REQ-001` (code chunk size bound)
- **Source issue**: `issues/20261107-055949_ragc001_code-chunk-size.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-084815_ragc001_code-chunk-size.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-092152
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`