# Implementation procedure: `tests/test_memory_extract.py` (chunking test cases)

Source plan: `plans/20260719-095637_plan.md` ("Enable the persistent memory layer by default and add the
missing chunking step", requirement `requires/done/20260714_15_require.md`), Implementation step 1
(test coverage) and the plan's Validation plan row "Tests (extract)".

`implementations/done/20260610-114915_extract_py.md` and `implementations/done/20260606-194532_extract.md`
exist under `implementations/done/` and touch extraction tests, but predate this batch and address the
original extraction-policy test suite, not chunking. No doc proposes adding chunk-boundary test cases.
Flagged as checked, not a genuine overlap.

## Goal

Add unit test coverage for `_split_content` and for the chunked, multi-entry behavior of
`_try_extract_from_assistant`/`_try_extract_from_user`/`extract_memories`, so the new chunking stage
(paired `scripts/agent/memory/extract.py` implementation doc) is behavior-locked before it ships.

## Scope

**In scope**
- New test cases covering: content under the limit (single chunk, unchanged passthrough), content over
  the limit split cleanly on paragraph (`\n\n`) boundaries, a single paragraph exceeding the limit
  (hard-cut fallback), and `extract_memories` producing multiple `MemoryEntry` rows (all sharing
  `session_id`/`turn_id`/`project`/`repo`/`branch`, differing only in `content`/`summary`/`memory_id`)
  from one over-long assistant message.
- A test confirming no existing behavior regresses: short/normal-length content still yields exactly one
  entry per qualifying message (all 17 existing tests in this file must keep passing unmodified).

**Out of scope**
- `tests/test_memory_layer.py`, `tests/test_agent_factory.py`, `tests/test_embedding_client.py` — listed
  in the plan's Validation plan as regression checks to re-run, not files to edit; no chunking-specific
  assertions are added there by this plan.
- Testing `ingestion.py`'s per-entry loop directly — covered by re-running
  `tests/test_memory_layer.py`/`tests/test_memory_consistency.py`/`tests/test_agent_cmd_memory.py`
  unchanged (per the paired `extract.py` and plan-level Validation plan), not by new tests in this file.

## Assumptions

1. Confirmed by direct read of `tests/test_memory_extract.py` (238 lines, `TestExtractMemories` at line
   21, `TestClassifyContent` at line 199): **no existing test in this file sets `max_content_chars` above
   the 500-char default or otherwise exercises truncation** — the longest content used today is
   `"A " * 100"` (200 chars, `test_extracts_episodic_qa_for_long_answer`, line 61-68) and
   `"The rule is that we should always follow the policy {i} constraint decided. " * 5` (~385-390 chars,
   `test_does_not_exceed_max_entries`, line 102-119), both well under the 500-char default limit. This
   matches the plan's own claim (`grep -rn "max_content_chars" tests/` only hits an unrelated
   factory-wiring assertion in `tests/test_agent_factory.py:60`) — confirmed independently in this cycle
   by inspection of every content literal in this file. **No existing test needs modification**; new
   tests are a pure addition.
2. The test helper `_hist(*pairs) -> list[HistoryMessage]` (line 16-18) and the existing import block
   (`from agent.memory.extract import (MIN_USER_CONTENT_CHARS, _classify_content, extract_memories)`,
   lines 8-12) are reused as-is; new tests import `_split_content` locally inside the test function body
   (matching this file's existing convention of local imports for private symbols, e.g. `MAX_ENTRIES` at
   line 117, `_SEMANTIC_KEYWORDS` at line 203) rather than adding it to the module-level import block.
3. `extract_memories`'s default `max_content_chars=500` (`extract.py:303`) means chunking tests must use
   content deliberately longer than 500 chars, or pass an explicit smaller `max_content_chars` to
   `extract_memories(...)` to keep test content short and readable. The latter is preferred for
   readability (matches this file's existing style of small, focused literals) — e.g.
   `extract_memories(history, max_content_chars=50)` with a ~150-char assistant message.
4. Per the paired `extract.py` doc's Assumption 4, classification/importance now run on the **full**
   content before splitting — so a test message must still satisfy `_classify_content`'s keyword/length
   thresholds (`MIN_CONTENT_CHARS=80`, semantic/failure keyword regexes) on its full, unsplit form to
   produce any entries at all; this is unchanged from today's behavior and existing tests already
   demonstrate the pattern (e.g. line 34-45).

## Implementation

### Target file

`tests/test_memory_extract.py`

### Procedure

1. Add a new test class `TestSplitContent` (after `TestExtractMemories`, before `TestClassifyContent`,
   or at end of file — placement not load-bearing) with cases:
   - `test_content_under_limit_returns_single_chunk`: short content, `max_chars` larger than
     `len(content)` → `_split_content(content, max_chars) == [content]`.
   - `test_content_over_limit_splits_on_paragraph_boundary`: two `"\n\n"`-separated paragraphs, each
     individually under `max_chars` but combined over it → asserts `len(result) == 2` and
     `result == [para1, para2]` (or the greedily-packed equivalent if more than 2 short paragraphs are
     used — assert exact expected list for a deterministic case).
   - `test_single_paragraph_exceeding_limit_hard_cuts`: one paragraph (no `"\n\n"`) longer than
     `max_chars` → asserts every returned chunk has `len(chunk) <= max_chars`, chunks concatenate back to
     the original content (`"".join(result) == content`), and `len(result) == ceil(len(content) / max_chars)`.
   - `test_max_chars_zero_or_negative_disables_splitting`: `max_chars=0` → `_split_content(content, 0) ==
     [content]` regardless of length (mirrors today's `max_content_chars > 0` guard).
2. Add new test methods to `TestExtractMemories`:
   - `test_over_limit_assistant_message_yields_multiple_entries`: an assistant message whose content
     exceeds a small explicit `max_content_chars` (e.g. `50`) and satisfies classification (contains
     semantic/failure keywords or exceeds `MIN_CONTENT_CHARS*2` for the plain-conversation path) →
     `extract_memories(history, max_content_chars=50)` returns `len(result) > 1`; assert all returned
     entries share the same `session_id`/`turn_id`/`project`/`repo`/`branch`/`memory_type`/`source_type`
     and have distinct `memory_id`s; assert the concatenation of all entries' `content` (in return order)
     reconstructs the original message content losslessly (no data discarded — the plan's core
     acceptance criterion).
   - `test_over_limit_user_rule_message_yields_multiple_entries`: same shape as above but for a user
     message with semantic keywords, verifying the new `max_content_chars` parameter on
     `_try_extract_from_user` is actually wired through `extract_memories`'s user-branch call site (this
     directly tests the fix for the missing `max_content_chars` pass-through noted in the paired
     `extract.py` doc's Assumption 3/procedure step 4).
   - `test_under_limit_message_still_yields_single_entry`: a regression guard — content just under
     `max_content_chars` still yields exactly one entry (no accidental splitting at the boundary).

### Method

Pure `pytest` unit tests, no fixtures beyond the existing `_hist` helper, no mocking (no I/O in
`extract.py`). Matches this file's existing flat function-per-test style inside `class Test...` groups.

### Details

No new test infrastructure. All new tests import `_split_content` and `extract_memories` from
`agent.memory.extract` (already the module under test). Recommended concrete boundary values: use
`max_chars`/`max_content_chars` values small enough (e.g. 20-50) that test literals stay short and the
expected chunk count is easy to assert exactly, following this file's existing preference for compact,
readable literals (e.g. `"A " * 100"`, `"x" * 90`).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/test_memory_extract.py && uv run ruff check tests/test_memory_extract.py` | 0 errors |
| Type check | `uv run mypy scripts/` (tests covered per `rules/coding.md` mypy note — pre-commit also runs mypy on `tests/`) | 0 new errors vs baseline |
| Targeted tests | `uv run pytest tests/test_memory_extract.py -v` | all pass, including all new chunking cases; all 17 pre-existing tests unmodified and still passing |
| No accidental truncation regression | `uv run pytest tests/test_memory_extract.py -k "over_limit or split_content" -v` | all new chunking-specific tests pass |
| Full suite | `uv run pytest -v` | no new failures vs pre-change baseline |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines (covers both this file and the paired `extract.py` change) |
