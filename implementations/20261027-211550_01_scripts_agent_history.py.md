# Implementation Procedure: Extend `compress()` fallback gating to token overflow and make the unit-drop condition token-aware

## Goal

When history compression is triggered by a **token-only** overflow (char limit not exceeded) and the summarizer returns `None`, apply the whole-unit fallback truncation with a token-aware drop condition, so the oversized history converges toward the limit instead of being resent unchanged to the backend every turn. (`REQ-001`, `REQ-002`, `REQ-004`, `REQ-005`)

## Scope

One production file, `scripts/agent/history.py`. Two changes:

1. `compress()` summary-`None` branch falls back when `over_char or over_token` (the token-only case no longer returns the unchanged history with `error="compression returned None"`).
2. `_apply_unit_drops` and the `_fallback_truncate` post-drop warning use a token-aware limit helper (`_is_over_any_limit` (new)).

No change to `CompressResult` schema, selection policy, protection logic, `_get_summary_text`, or `force_compress()`.

## Assumptions

- `_is_over_char_limit` guards on `self._char_limit > 0`; the new token check mirrors this with `self._token_limit > 0` (constructor default `0` = disabled, `scripts/agent/history.py` L87-90).
- Under default config (`tokenize_url=""`), the trigger (`count_tokens_async` via `_check_limits`) and the fallback (`count_tokens()`) both call `estimate_tokens()` — verified at `scripts/shared/token_counter.py` L94 (empty URL → `estimate_tokens()[0]`) and `scripts/agent/history.py` L183. Trigger and fallback therefore agree on the measurement.
- `_apply_unit_drops` receives pre-sorted, lowest-importance-first candidates from `_fallback_truncate` via `_drop_candidate_units`; the never-empty (`>= 1`) and protected-unit invariants are preserved unchanged.
- No existing `_is_over_any_limit` (new) helper exists in `scripts/agent/history.py` (verified by read).

## Design decisions

- Add one private helper `HistoryManager._is_over_any_limit(history)` returning `self._is_over_char_limit(history) or (self._token_limit > 0 and self.count_tokens(history) > self._token_limit)`. Call it from both `_apply_unit_drops` (drop condition) and `_fallback_truncate` (post-drop warning gate).
- In `compress()`, reuse the already-computed locals `over_char` / `over_token` (L276-277) in the summary-`None` guard instead of a second `_is_over_char_limit` scan — this removes a duplicated char scan and covers the token-only case in one expression.

## Alternatives considered

- A separate token-budgeted drop variant — rejected: the Plan's Unresolved Question resolves to reuse the existing unit-drop fallback with a token-aware limit check, not a new code path (`REQ-002`).
- Mode flags distinguishing char vs token — rejected: the char-path behavior is a strict subset of the new OR condition, satisfying `REQ-006` without any mode flag.

## Implementation

### Target file
`scripts/agent/history.py`

### Procedure
1. Add `_is_over_any_limit` (new) to `HistoryManager`, next to `_is_over_char_limit`.
2. In `_apply_unit_drops`, replace the `self._is_over_char_limit(new_history)` drop condition with `self._is_over_any_limit(new_history)`; keep the `and len(new_history) - len(unit) >= 1` never-empty guard exactly.
3. In `_fallback_truncate`, replace the post-drop warning gate `self._is_over_char_limit(new_history)` with `self._is_over_any_limit(new_history)` and extend the logged message to report both chars and tokens.
4. In `compress()`, change the summary-`None` branch from `if self._is_over_char_limit(history):` to `if over_char or over_token:` so the token-only case falls through to `_fallback_truncate`.

### Method
Two edits in one file: add one helper, swap two call sites to it, and change one guard expression. No new symbols beyond `_is_over_any_limit` (new).

### Details
- `_apply_unit_drops` becomes:
  ```python
  if self._is_over_any_limit(new_history) and len(new_history) - len(unit) >= 1:
  ```
- `_fallback_truncate` post-drop warning becomes:
  ```python
  if self._is_over_any_limit(new_history):
      logger.warning(
          "Fallback truncation could not bring context under limit: "
          "chars=%d limit=%d tokens=%d token_limit=%d",
          self.count_chars(new_history),
          self._char_limit,
          self.count_tokens(new_history),
          self._token_limit,
      )
  ```
  The char-only case now also logs its token estimate; the token-only case reports `token_limit`.
- `compress()` keeps `over_char` and `token_count, over_token` computed at L276-277; the guard reads:
  ```python
  if summary_text is None:
      if over_char or over_token:
          return self._fallback_truncate(history)
      return history, CompressResult(
          compressed_count=0,
          protected_count=0,
          summary_added=False,
          error="compression returned None",
      )
  ```
  The `error` branch now fires only when neither hard limit holds (truly under-limit), matching today's under-limit behavior.
- `force_compress()` sets `char_limit=1` → `over_char=True`; unaffected.
- `CompressResult` is unchanged; `_fallback_truncate` already returns `is_fallback=True`, `compressed_count=dropped` (`REQ-004`).

## Compatibility considerations

- `compress()` callers (`conversation_state_manager.handle_history_compression`) persist whenever `compressed_count > 0`; a fallback-produced history is persisted identically to the char path. No caller change.
- Char-path behavior is a strict subset of the new condition: when only `over_char` holds, results are byte-for-byte identical to today. Existing char-path tests pass unchanged (`REQ-006`).

## Security considerations

- `count_tokens()` is a read-only single-pass estimate; no injection or untrusted-execution surface is introduced. The fallback runs only in the summarizer-failure path.

## Rollback considerations

- Single logical commit touching `scripts/agent/history.py`, its tests, and the doc; rollback is `git revert`. No config, schema, or deployed-state change.

## Validation plan

- Unit (new): `uv run pytest tests/agent/test_history_manager.py -q -k "token and fallback or over_limit"` — the new token-only fallback cases (`T-001`..`T-003`) pass.
- Regression (existing): `uv run pytest tests/agent/test_history_manager.py tests/agent/test_history_compression_consistency.py tests/agent/test_regression_history_compress_reload.py` — existing cases pass unchanged (`AC-004`). Two named tests assert `error='compression returned None'` + `is_fallback=False`: `test_returns_original_and_error_when_llm_fails_under_limit_explicit` and `test_returns_original_and_error_when_llm_returns_empty_summary_under_limit`. Both are actually token-only overflow cases (char_limit=999999, token_limit=5, six 400-char messages ~= 600 tokens), so REQ-001 flips them to the fallback path; they are updated in the Row 2 test procedure, not left as-is.
- Consumers: `uv run pytest tests/agent/ -q -k "history or compress or rag_export"` — no regressions in compress callers.
- Static: `uv run ruff check scripts/agent/history.py` and `uv run mypy --no-namespace-packages scripts/agent/history.py` — clean.
- Full suite: `uv run pytest tests/` green.

## Completion criteria

- `compress()` falls back on `over_char or over_token` when the summary is `None`; the token-only case no longer returns `error="compression returned None"`.
- `_apply_unit_drops` and the `_fallback_truncate` warning use `_is_over_any_limit` (new) (char OR token).
- Token-path fallback reports `is_fallback=True`, `compressed_count` = dropped messages, and increments `stat_fallback_truncate_count` (`AC-001`).
- Repeated `compress()` in the failure state shortens history (`AC-002`); tool rows are never orphaned and history stays non-empty (`AC-003`); all existing tests pass (`AC-004`).

## Out of Scope

- Improving token estimation accuracy.
- Changing summarizer retry/timeout policy.
- `CompressResult` schema, selection policy, protected-turn handling, `_get_summary_text`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `_is_over_any_limit` (new), swap the two call sites, and change the `compress()` summary-`None` guard to `over_char or over_token` | Pending | — | — | |
| 2 | Add token-only fallback regression tests; run the validation sequence | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-004`, `REQ-005`
- **Source issue**: issues/20261026-224931_history001_token-overflow-compression-fallback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074212_history001_token-overflow-compression-fallback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-211550
- **Related target files**: scripts/agent/history.py
