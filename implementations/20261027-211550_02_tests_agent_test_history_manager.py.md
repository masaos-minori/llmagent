## Goal

Add regression tests for the token-only-overflow fallback path (`REQ-001`, `REQ-003`, `REQ-004`, `REQ-005`) and correct two existing tests in `TestFallbackTruncate` that are mislabeled as "under limit" but are actually token-only overflow cases. Under `REQ-001` those two tests flip from asserting no-fallback to asserting the fallback path, so they must be updated or the suite breaks.

## Scope

One test file, `tests/agent/test_history_manager.py`, class `TestFallbackTruncate` (currently L778-1016):

1. Add three new async tests: T-001 (token-only overflow + summarizer `None` → shortened + `is_fallback=True`), T-002 (tool-round integrity under the token fallback), T-003 (repeated `compress()` stays bounded).
2. Update the two existing tests `test_returns_original_and_error_when_llm_fails_under_limit_explicit` (L939) and `test_returns_original_and_error_when_llm_returns_empty_summary_under_limit` (L964): they currently assert the OLD no-fallback behavior for a token-only overflow; replace their assertions with the new fallback assertions and rename them to drop the misleading under-limit suffix.

No production code and no docs touched here (those are Rows 1 and 3).

## Assumptions

- `_make_manager` accepts a `token_limit` kwarg (constructor default `0` = disabled) — `tests/agent/test_history_manager.py` L32. Tests therefore set limits explicitly rather than reading `config/agent.toml` (resolves `UNK-01`).
- Under default config (`tokenize_url=""`), `count_tokens()` uses the category-aware `estimate_tokens()` (`scripts/agent/history.py` L183; `scripts/shared/token_counter.py` L94), the same estimator the trigger uses.
- The two tests being updated set `char_limit=999999` and `token_limit=5` with six 400-char messages (~600 tokens). They are **token-only overflow**, not under-limit: `over_char=False`, `over_token=True`. Currently `compress()` returns them unchanged with `error="compression returned None"` / `is_fallback=False`; after `REQ-001` they fall through to `_fallback_truncate`.
- `_fallback_truncate` returns `CompressResult(is_fallback=True, compressed_count=dropped, summary_added=False)` with `error=None` (default) — `scripts/agent/history.py` L322-327.
- The never-empty guard (`len(new_history) - len(unit) >= 1`) means with `token_limit=5` and ~100 tokens per message the token-only fallback drops down to a single remaining message.

## Design decisions

- T-001 mirrors the existing char-path `test_compress_calls_fallback_when_llm_fails_and_over_limit` (`TestFallbackTruncate`, L921) but forces token-only overflow by setting `char_limit` huge and `token_limit` small, then asserts the fallback succeeded instead of the unchanged-history error path.
- The two flipped tests are corrected in place rather than deleted: they still exercise the "summarizer unavailable during a real overflow" branch, now asserting the correct (post-`REQ-001`) outcome. Their under-limit names are renamed because they never described an under-limit case.

## Alternatives considered

- Deleting the two flipped tests and relying on new tests alone — rejected: they already cover a valid branch (LLM failure during token overflow) and correcting them preserves coverage while removing a now-failing assertion (`REQ-006`).

## Implementation

### Target file
`tests/agent/test_history_manager.py`

### Procedure
1. In `TestFallbackTruncate`, add `test_compress_falls_back_on_token_only_overflow_when_llm_fails` (new) (T-001) — see Details.
2. Add `test_compress_token_only_fallback_preserves_tool_rounds` (new) (T-002) and `test_compress_token_only_fallback_stays_bounded_repeated` (new) (T-003) — see Details.
3. Update `test_returns_original_and_error_when_llm_fails_under_limit_explicit` (L939): replace its no-fallback assertions with the fallback assertions below and rename it to `test_compress_falls_back_on_token_overflow_when_llm_fails` (new).
4. Update `test_returns_original_and_error_when_llm_returns_empty_summary_under_limit` (L964): same correction; rename to `test_compress_falls_back_on_token_overflow_when_llm_returns_empty_summary` (new).

### Method
Add three new async tests and correct two existing ones, all inside `TestFallbackTruncate`. One file, one class.

### Details
- T-001 (token-only overflow + summarizer fails → fallback). Geometry reuses the passing char-path test's message layout, swapping the limit roles:
  ```python
  @pytest.mark.asyncio
  async def test_compress_falls_back_on_token_only_overflow_when_llm_fails(self) -> None:
      mock_http = AsyncMock(spec=httpx.AsyncClient)
      mock_http.post.side_effect = httpx.RequestError("fail")
      # Under char_limit, over token_limit -> token-only overflow triggers compression
      mgr = _make_manager(char_limit=999999, token_limit=5, compress_turns=1, http=mock_http)
      h = _history(
          ("user", "x" * 400),
          ("assistant", "y" * 400),
          ("user", "z" * 400),
          ("assistant", "w" * 400),
          ("user", "a" * 400),
          ("assistant", "b" * 400),
      )
      result, cr = await mgr.compress(h)
      assert cr.is_fallback is True
      assert cr.error is None
      assert mgr.stat_fallback_truncate_count == 1
      assert 0 < len(result) < len(h)
  ```
- T-002 (tool-round integrity). Build a history whose oldest droppable unit holds an assistant `tool_calls` message followed by its tool result. After the token fallback drops whole units, assert the pair is either both retained or both dropped — never split (an assistant with `tool_calls` must not be left without its tool row, and vice versa) — and that the protected tail (if `protect_turns>0`) is intact. A unit-level check is cleanest: group `result` into turn units (a unit starts at a `user` message and runs to the next `user`) and assert no unit mixes a kept assistant `tool_calls` with a dropped tool row.
- T-003 (bounded under repeated failure). Call `compress()` twice in the token-only-overflow + summarizer-failure state; assert the second call either shortens further or the history is at its protected/minimal size with the "could not bring under limit" warning logged — i.e. no silent unchanged-success. `assert len(second_result) <= len(first_result)` and (`len(second_result) < len(first_result)` or the warning was logged).
- Corrected assertions for the two renamed tests (replace the old `assert result == h` / `assert cr.error is not None` / `assert cr.is_fallback is False`):
  ```python
  assert cr.is_fallback is True
  assert cr.error is None
  assert mgr.stat_fallback_truncate_count == 1
  assert 0 < len(result) < len(h)
  ```

## Compatibility considerations

N/A: test-only change; `scripts/agent/history.py` is untouched by this document (Row 1). The corrected tests are required for `AC-004` — leaving them asserting the old behavior would fail the suite after Row 1's change.

## Security considerations

N/A: test-only change, no new runtime surface.

## Rollback considerations

N/A: revert the commit. No config, schema, or deployed-state change.

## Validation plan

- Unit: `uv run pytest tests/agent/test_history_manager.py -q` — all pass, including the three new token-only cases and the two corrected tests.
- Consumers: `uv run pytest tests/agent/ -q -k "history or compress or rag_export"` — no regressions.
- Static: `uv run ruff check tests/agent/test_history_manager.py` and `uv run mypy --no-namespace-packages tests/agent/test_history_manager.py` — clean.
- Full suite: `uv run pytest tests/` green.

## Completion criteria

- T-001 asserts `is_fallback=True`, `error=None`, `stat_fallback_truncate_count == 1`, and a shortened non-empty history for the token-only-overflow + summarizer-failure state.
- T-002 asserts no tool row is orphaned after the token fallback; T-003 asserts repeated calls stay bounded (no silent unchanged success).
- The two previously-mislabeled tests now assert the fallback outcome and carry non-misleading names.
- The whole file passes `ruff`/`mypy` and the history/compression test suite (`AC-004`).

## Out of Scope

- Production logic (`scripts/agent/history.py`) — Row 1.
- Docs update (`docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`) — Row 3.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three token-only fallback regression tests and correct the two mislabeled token-overflow tests | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`
- **Source issue**: issues/20261026-224931_history001_token-overflow-compression-fallback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074212_history001_token-overflow-compression-fallback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-211550
- **Related target files**: tests/agent/test_history_manager.py
