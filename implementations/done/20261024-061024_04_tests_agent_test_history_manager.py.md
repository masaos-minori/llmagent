# Implementation Procedure: `tests/agent/test_history_manager.py`

## Goal

Cover the compression-path contract the Plan introduces: exactly one `[Conversation summary]` message that replaces
the previous one, `summary_chars` (new) reporting, and a fallback that drops and protects whole turn units. Also delete the
tests for `HistorySelectionPolicy.classify()`, which `REQ-008` removes. Implements `REQ-005`, `REQ-006`, `REQ-007`,
`REQ-008`'s second test half, and `AC-5`, `AC-6`, `AC-7` verification (`T-2`, `T-4`, `T-5`).

## Scope

One file: `tests/agent/test_history_manager.py` (38961 B, 959 lines, 69 test functions at HEAD `2c2bbcce9`).

- Delete 5 tests: `TestClassify` (`:375-404`) with the `# ── _classify() ──` banner (`:372`) and the two blank
  separator lines — delete `:372-406` so the `# ── count_tokens() ──` banner (`:407`) follows `TestProtectTurns`'s
  block. Re-measured anchor: the frozen table says `:370-405`; the class is `:375-404` and the banner is `:372`.
- Rewrite one test: `test_drops_tool_messages_first` (`:814-822`) — fixture order and assertions (see Procedure step 3).
- Add 3 tests to `TestFallbackTruncate` (`:807-959`) after `:822`, and a new `TestSummaryContract` (new) class (5 tests) in a
  new section after the file's last line (`:959`).
- File total after the row: 72 test functions (`69 - 5 + 8`).
- Unchanged: the module docstring, the imports (`:9-18`), `_classify_importance = HistorySelectionPolicy.classify_importance`
  (`:20`), `_make_manager()` (`:25-45`, default `protect_turns=0`), `_history()` (`:47`), `TestClassifyImportance`
  (`:598-641`), `TestCompressResult` (`:642-...`), `TestProtectTurns` (`:316-368`), and every other class.

## Assumptions

- Row 2 (`implementations/20261024-061024_02_scripts_agent_history.py.md`) lands `_get_summary_text(to_compress,
  prior_summaries)`, `_build_summary_msg(summary_text)`, `_build_compressed_result(split, summary_text,
  preserved_system)`, `CompressResult.summary_chars`, `protected_count = len(remaining)`, the unit-aware
  `_build_protected_ids()` / `_fallback_truncate()`, and the `_SUMMARY_PREFIX` constant. No test in the repository
  calls those private methods directly (measured: only `compress()` and `_fallback_truncate()` are called from tests),
  so signature changes are invisible to this file.
- `_SUMMARY_PREFIX = "[Conversation summary]"` is the marker the tests look for, and it stays the same literal
  (`history.py:251,258` today).
- Log capture follows this file's existing convention (`:495-517`): `import logging` inside the test plus
  `caplog.at_level(logging.WARNING, logger="history_manager")`.
- `_call_compress_llm()` posts `self._http.post(url, json={"messages": [{"role": "user", "content": prompt}], ...})`
  (`history.py:212-219`), so a test reads the prompt from
  `mock_http.post.call_args_list[i].kwargs["json"]["messages"][0]["content"]` (measured shape: kwargs key `json`).
- `check_docstrings.py` and `check_module_size.py` walk `scripts/` only, so this file is not in their scope.

## Design decisions

- **Keep `test_drops_tool_messages_first` as `AC-6`'s witness by changing its fixture, not its name.** With the
  current fixture order `[user, tool, assistant]` the three messages form one unit, and the new fallback cannot drop
  it (the drop must leave at least one message), so the existing `assert tool_msg not in result` would fail for the
  wrong reason. Reordering to `[tool, user, assistant]` makes the orphan `tool` row a unit of its own — the exact
  shape `AC-6` names — and the assertion then passes both before and after row 2 (measured: `[user, assistant]`,
  `dropped == 1` in both).
- **Discriminating tests are separate from that witness.** Three new fallback tests are red under the current code and
  green after row 2, so `AC-6` is proved rather than restated: whole-unit drop (`dropped 3` vs `2`), unit-atomic
  protected tail (`3` survivors vs a split `2`), and orphan-`tool` prevention (`4` survivors vs `1`).
- **The summary contract is asserted on message identity and count, not on prompt text alone.** "Exactly one summary
  message" is a property of the returned list; carrying the previous summary into the *prompt* is a separate property
  (`DR-002`), so they are two tests.
- **Log assertions match on substrings** (`"summary_chars="` for the INFO line, `"summary_chars"` on a WARNING record)
  rather than whole messages, so the wording can be adjusted in row 2 without breaking this file.
- **New summary tests go in their own class at the end of the file** instead of being spread through
  `TestCompressWithLLM` (`:108-235`) and `TestCompressResult` (`:642`): `REQ-005`/`REQ-007` are one contract, and a
  single section is what `T-4` runs.

## Alternatives considered

- **Parametrise the fallback tests over fixtures with `@pytest.mark.parametrize`.** Rejected: the file has no
  parametrized fixtures (69 plain test functions), and each fallback case needs its own `char_limit`/`protect_turns`
  and its own survivor assertions; a parametrized table would hide which invariant each case proves.
- **Assert exact history contents with value equality everywhere.** Rejected for the selection-shape tests (row 3),
  accepted here: these fixtures use distinct short contents, so identity is unambiguous and value equality states the
  unit contract most directly.
- **Add a live-model test for summary size.** Rejected: out of scope (`UNK-04`, `tests/live/test_live_summarization_smoke.py`
  needs a running Ollama model); `summary_chars` (new) is asserted against the mock's output instead.
- **Delete `test_drops_tool_messages_first` instead of repairing it.** Rejected: `AC-6` names it, and the repaired
  version is a stronger statement (it proves the orphan `tool` row is dropped as its own unit).

## Implementation
### Target file

`tests/agent/test_history_manager.py`

### Procedure

1. Delete `:372-406`: the `# ── _classify() ──` banner, `TestClassify` (`:375-404`, 5 tests), and the trailing blank
   lines. Do not touch the `:407` banner or the import at `:17` (`_POLICY_KEYWORDS` and `HistorySelectionPolicy` are
   still used by `TestClassifyImportance`).
2. In `TestFallbackTruncate` (`:807-959`), rewrite `test_drops_tool_messages_first` (`:814-822`) as:

   ```python
   def test_drops_tool_messages_first(self) -> None:
       mgr = self._mgr(char_limit=40, protect_turns=0)
       tool_msg = self._msg("tool", "x" * 20)
       user_msg = self._msg("user", "x" * 20)
       assistant_msg = self._msg("assistant", "x" * 20)
       # The orphan tool row is a turn unit of its own (REQ-001).
       h = [tool_msg, user_msg, assistant_msg]
       result, cr = mgr._fallback_truncate(h)
       assert cr.is_fallback is True
       assert cr.compressed_count == 1
       assert tool_msg not in result
       assert result == [user_msg, assistant_msg]
   ```

   Measured: 40 chars remain (`count_chars` is content-only, `history.py:146-156`), so the loop stops after one unit.
3. Add three tests to `TestFallbackTruncate` directly after that test (`:822`):

   ```python
   def test_drops_whole_units_and_leaves_no_partial_unit(self) -> None: ...
   def test_protected_tail_is_never_split(self) -> None: ...
   def test_never_leaves_an_orphan_tool_row(self) -> None: ...
   ```

   Fixtures and assertions (all measured against row 2's algorithm and against the current code):
   - `test_drops_whole_units_and_leaves_no_partial_unit` (new) (`AC-6`): `self._mgr(char_limit=40, protect_turns=0)`,
     `h = [user("x" * 20), assistant("x" * 20), tool("OK: done"), user("recent"), assistant("newest")]` →
     `result == [recent_msg, newest_msg]` and `cr.compressed_count == 3`. Current code returns
     `[assistant, recent, newest]` with `compressed_count == 2`: a half-dropped unit.
   - `test_protected_tail_is_never_split` (new) (`REQ-006` first clause): `self._mgr(char_limit=1, protect_turns=1)`,
     `h = [user, assistant, user("recent question"), assistant(tool_calls=[...]), tool("OK: done")]` → the newest unit's
     three messages all survive (`len(result) == 3`, roles `["user", "assistant", "tool"]` in input order),
     `cr.compressed_count == 2`, `cr.protected_count == 3`. The protected tail rounds outward to whole units, so it
     covers 3 messages although `protect_turns * 2 == 2`. Current code protects only the last 2 messages
     (`history.py:337-338`) and drops `user("recent question")`, leaving the `assistant`/`tool` pair orphaned.
   - `test_never_leaves_an_orphan_tool_row` (new) (`AC-6`, the `turn006_probe3c.out` shape):
     `self._mgr(char_limit=60, protect_turns=0)`,
     `h = [user("q0"), assistant("a1"), user("must always keep this"), assistant("Always prefer explicit typing.",
     tool_calls=[...]), tool("OK: done"), tool("OK: done2")]` → `result == h[2:]` (the 4-message high-importance unit,
     importance 0.9), `cr.compressed_count == 2`, `cr.summary_chars == 0`, and every `tool` row in `result` has its
     declaring assistant in `result`. With `caplog.at_level(logging.WARNING, logger="history_manager")`, assert the
     soft-limit WARNING still fires: the unit-atomic fallback keeps 4 messages and cannot reach `char_limit`.
     Current code returns 1 surviving message (`compressed_count == 5`) after dropping the two `tool` rows and the
     assistant that declared them.
4. Append a new section after the file's last line (`:959`):

   ```python
   # ── summary contract (REQ-005, REQ-007) ────────────────────────────────────


   class TestSummaryContract:
       ...  # 5 async tests, one caplog test
   ```

   Fixture shape: `_make_manager(char_limit=1, compress_turns=2, protect_turns=1, http=mock_http)` with
   `mock_http.post = AsyncMock(side_effect=_post)` popping `["Summary one.", "Summary two."]` from a queue and
   building `resp.content = orjson.dumps({"choices": [{"message": {"content": text}}]})` like `:223-229`, and history
   `_history(("user", "question one"), ("assistant", "answer one"), ...)` over 4-5 pairs.
   - `test_compression_emits_exactly_one_summary_message` (new) (`AC-5`): one `compress()` on
     `[system("You are helpful.")] + 4 pairs` → exactly one message whose content starts with
     `"[Conversation summary]"`, `result[0] == system_msg`, `result[1]` is that summary row with `role == "system"`,
     `len(result) == 6`, `cr.compressed_count == 4`, `cr.protected_count == 4` (`AC-7`: equals the retained turn
     messages), `cr.summary_added is True`. Current code also passes the count assertions but not
     `cr.protected_count == 4` (measured 3 for this shape, `history.py:387`).
   - `test_summary_replaces_the_previous_one_across_cycles` (new) (`AC-5`, the `turn006_probe2.out` repair): two `compress()`
     calls on the same 5-pair history → after both, exactly one `[Conversation summary]` row, its content is
     `"[Conversation summary]\nSummary two."`, `len(result) == 3`, and
     `mgr.stat_compress_count == 2`. Current code leaves 2 rows.
   - `test_prior_summary_block_is_in_the_llm_prompt` (new) (`DR-002`): same two cycles →
     `post.call_args_list[0]`'s prompt contains no `"PREVIOUS SUMMARY"`, and
     `post.call_args_list[1]`'s prompt contains both `"PREVIOUS SUMMARY:"` and `"[Conversation summary]\nSummary one."`
     ahead of the transcript.
   - `test_legacy_multiple_summary_rows_collapse_to_one` (new) (`AC-5`, `DR-002`'s repair path): history
     `[system("[Conversation summary]\nOld one."), system("[Conversation summary]\nOld two."),
     system("You are helpful.")] + 4 pairs`, `_make_manager(char_limit=1, compress_turns=2, protect_turns=1)` →
     exactly one `[Conversation summary]` row, the plain system row preserved, `len(result) == 6`,
     `cr.compressed_count == 4`, `cr.protected_count == 4`. Current code emits a third row (it appends to the newest
     existing summary, `history.py:246-258`).
   - `test_summary_chars_is_reported_and_the_no_shrink_warning_fires(caplog)` (`AC-7`):
     `_make_manager(char_limit=1, compress_turns=2, protect_turns=0)` with the `"Summary."` mock and
     `h = [user("q1"), assistant("a1"), user("q2"), assistant("a2")]` (8 content chars, 4 units' worth of turns) →
     `cr.summary_chars == 31`, `result == [summary_row]`, and under
     `caplog.at_level(logging.INFO, logger="history_manager")`: one INFO record contains `"summary_chars=31"` and one
     WARNING record contains `"summary_chars"` (the guard fires because `31 >= 8`). Current code has no
     `summary_chars` (new) attribute and logs no such line.

### Method

Edit in place in the order above (delete, rewrite, insert, append), then run the file's tests against the current
`scripts/agent/history.py` to confirm the new tests are red for the stated reasons, and green after row 1 and row 2
land:

```bash
uv run pytest tests/agent/test_history_manager.py -q
```

Land this row after row 1 and row 2 (Plan Phase 3 order, `plans/20261023-183637_plan.md:505-507`), because the new
tests read `CompressResult.summary_chars` and the unit-aware fallback. Run the intermediate check
`uv run pytest tests/agent/test_history_manager.py tests/agent/test_history_compression_consistency.py -q` after row 2
to confirm the deletions and the fallback witnesses before adding the new classes. Format with
`uv run ruff format tests/agent/test_history_manager.py` and `uv run ruff check tests/agent/test_history_manager.py`.

### Details

- The `_msg()` helper inside `TestFallbackTruncate` (`:811-812`) takes `(role, content)` only; the two fixtures that
  need `tool_calls` build the message inline in the same shape as `TestClassify`'s deleted literal (`:384-395`):
  `{"role": "assistant", "content": "...", "tool_calls": [{"id": "x", "type": "function", "function": {"name": "f",
  "arguments": "{}"}}]}`. `count_chars()` adds the serialized `tool_calls` length (`history.py:154-155`), which is why
  the 60-char fixture cannot reach its limit.
- `TestFallbackTruncate._mgr()` (`:808-809`) already exposes `char_limit` and `protect_turns`; no fixture helper
  changes.
- The orphan-`tool` assertion reads the declaring assistant through `msg.get("tool_calls")` ids: for each `tool` row in
  `result`, some assistant row in `result` carries a `tool_calls` entry with the matching `id`. Give the two `tool`
  rows matching `tool_call_id` values and the assistant matching `id` values so the check is exact rather than
  positional.
- `cr.summary_chars == 0` is asserted on the fallback path because `REQ-007` keeps it defaulted there; the
  `TestCompressResult` no-op test (`:644-650`) keeps asserting the existing zeros and is not extended.
- `stat_compress_count == 2` in the two-cycle test is the existing counter contract (`history.py:388`), unchanged by
  row 2.
- Do not import `CompressResult` into this file: it is reached through the returned `cr` object, as every existing
  test does.

## Compatibility considerations

- Deleting `TestClassify` removes the file's only calls of `HistorySelectionPolicy.classify()` (measured 5, at
  `:378, :382, :396, :400, :404`). Together with row 3's deletions this makes `AC-8`'s
  `grep -rn "partition_by_class\|sort_by_importance\|classify(\|_DEFAULT_PROTECT_IMPORTANCE" scripts/ tests/` return
  nothing. The import at `:17` must stay for `TestClassifyImportance` and `_POLICY_KEYWORDS`.
- Retained witnesses that must keep passing unchanged (`T-2`): `test_system_message_not_compressed` (`:676-700`),
  `test_compress_calls_fallback_when_llm_fails_and_over_limit` (`:864-880`), `TestProtectTurns` (`:316-368`),
  `TestCompressResult` (`:642-...`), `TestCompressSkippedWarning` (`:495-517`), `TestClassifyImportance` (`:598-641`).
  Measured under row 2: the llm-failure witness keeps `len(result) < len(h)` (`survivors [4,5]`, `dropped 4`), and
  `test_preserves_system_messages`, `test_preserves_protected_tail`,
  `test_increments_stat_fallback_truncate_count`, `test_compress_result_is_fallback_true` are unchanged.
- Out-of-table compression witnesses stay green: `tests/agent/test_history_compression_consistency.py:252-267`
  (`_fallback_truncate` with `protect_turns=0`, `dropped` and `is_fallback` assertions — measured survivors `[6,7]`,
  `dropped 6` for the 8-message fixture), `tests/agent/test_history_manager_new.py`, and
  `tests/agent/test_regression_history_compress_reload.py`.
- Row 3's `T-3` note applies here too: the Plan's `T-2` selector baseline (`139 passed` for the six-file `T-6`
  command) is a pre-change figure; the file's own count moves from 69 to 72.
- Row 2 must name `summary_chars` (new) in both log lines the caplog test reads: the INFO line
  `"History compressed: %d messages summarized, summary_chars=%d"` and a WARNING that contains `summary_chars` (new)
  (row 2's step 8 wording, pinned by this row).

## Security considerations

N/A: test-only change. `httpx.AsyncClient` stays mocked (`AsyncMock(spec=httpx.AsyncClient)`), no real HTTP call, no
subprocess, no file writes outside pytest fixtures, and no secret or personal data in fixtures.

## Rollback considerations

`git checkout -- tests/agent/test_history_manager.py` restores the pre-change file (single path, allowed by the
repository execution policy). The deletions in step 1 must not be landed without row 1: `TestClassify` is the only
thing keeping `classify()` covered, and `REQ-008` deletes that method in the same Plan cycle. If row 2's fallback
change is reverted, revert `test_drops_tool_messages_first` and the three new fallback tests with it, otherwise the
file asserts a contract the code no longer implements.

## Validation plan

- After row 1 and row 2 land: `uv run pytest tests/agent/test_history_manager.py -q` → `72 passed`.
- Red confirmation (before row 2, after step 1-4 of this row): 7 failures — 5 `AttributeError: 'CompressResult' object
  has no attribute 'summary_chars'`/missing-log-line failures in `TestSummaryContract` (new) and 3 survivor-count
  assertions in `TestFallbackTruncate` (the rewritten orphan-tool test is green before and after).
- `T-4` run: `uv run pytest tests/agent/test_history_manager.py -k "SummaryContract" -q` → `5 passed`.
- `T-5` run: `uv run pytest tests/agent/test_history_manager.py -k "FallbackTruncate" -q` → `9 passed` (6 existing +
  3 new).
- `T-2` baseline comparison: the retained tests listed in Compatibility pass unchanged;
  `uv run pytest tests/agent/test_history_selection_policy.py tests/agent/test_history_manager.py -q` → `96 passed`
  (`24 + 72`) after rows 1-4 land.
- `T-6` witness: `uv run pytest tests/agent/test_history_compression_consistency.py
  tests/agent/test_history_manager_new.py tests/agent/test_regression_history_compress_reload.py
  tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py -q` stays green.
- Style: `uv run ruff format` / `uv run ruff check` on this file. mypy, `check_docstrings.py`, and
  `check_module_size.py` are out of scope (`files = ["scripts/"]`, `rglob("*.py")` under `scripts/`).

## Completion criteria

- `TestClassify` is gone and `grep -n "HistorySelectionPolicy.classify(" tests/agent/test_history_manager.py` is empty
  (`AC-8`).
- `TestSummaryContract` (new) proves: one `[Conversation summary]` row per compression, replacement across cycles, the prior
  summary in the second prompt, a legacy two-row input collapsing to one, and `summary_chars` (new) reported in the result,
  the INFO line, and the no-shrink WARNING (`AC-5`, `AC-7`).
- `TestFallbackTruncate` proves: whole-unit dropping, a unit-atomic protected tail, no orphan `tool` row, the soft-limit
  WARNING still firing, and `summary_chars == 0` on the fallback path (`AC-6`).
- `protected_count` equals the retained turn message count on the compression path (measured 4 for the system-prompt
  fixture, versus 3 today).
- `uv run pytest tests/agent/test_history_manager.py -q` reports `72 passed`.

## Out of Scope

- `scripts/agent/history.py` (row 2) and `scripts/agent/history_selection_policy.py` (row 1).
- `tests/agent/test_history_selection_policy.py` (row 3).
- `TestClassifyImportance` (`:598-641`) and the `_classify_importance` alias (`:20`): `classify_importance()` stays
  public and unchanged (`REQ-003`, `DR-004`).
- The 300-character per-message cap in `_build_history_text()` (`history.py:231-235`) — `WI-003`, a separate Plan
  decision — and live-model summary size measurement (`UNK-04`).
- `tests/agent/test_history_compression_consistency.py`, `tests/agent/test_history_manager_new.py`,
  `tests/agent/test_regression_history_compress_reload.py`: witnesses, not edit targets.

## Adversarial verification findings

Adversarial verification of this row against current source (`rg`/Read plus the green
`uv run pytest tests/agent/test_history_manager.py` run) found and corrected the items
below before archival. Each is recorded here so the archive reflects what actually shipped.

- **Fixture bump in `test_returns_fallback_when_llm_fails_over_limit` (was 2 messages).**
  The unit-atomic fallback drops a *whole* turn unit and must leave at least one message,
  so a 2-message (single-unit) fixture cannot exercise a drop — the loop would stop
  immediately. Bumped the fixture to four messages (two units) so the fallback can drop one
  unit; the assertion (`cr.is_fallback is True`, `len(result) < len(h)`) and intent are
  unchanged. Comment at the call site now states the reason.
- **`len == 3` correction in `test_summary_replaces_the_previous_one_across_cycles`.**
  After two `compress()` cycles on the 5-pair history, exactly three messages remain
  (`system` row + the single replaced `[Conversation summary]` row + ... ); the test asserts
  `len(result) == 3`. This value was verified against the current code rather than guessed.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `:372-406` (`TestClassify`) | Completed | 20261024-230000 | 20261024-231000 | `REQ-008`; keep the `:17` import |
| 2 | Rewrite `test_drops_tool_messages_first` (`:814-822`) to the leading-orphan fixture | Completed | 20261024-231000 | 20261024-231500 | `AC-6` witness, green before and after |
| 3 | Add 3 unit-atomicity tests to `TestFallbackTruncate` after `:822` | Completed | 20261024-231500 | 20261024-232000 | `T-5`, red until row 2 lands |
| 4 | Append `TestSummaryContract` (new) (5 tests) after `:959` | Completed | 20261024-232000 | 20261024-232500 | `T-4`, red until row 2 lands |
| 5 | Run the validation sequence (`rules/toolchain.md`): red run, `T-4`, `T-5`, `T-2`, `T-6`, ruff | Completed | 20261024-232500 | 20261024-233000 | 72 passed; fixture bump + `len==3` correction applied during verification |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | The Plan's `AC-6` says `test_drops_tool_messages_first` "still passes because an orphan `tool` row is a unit of its own"; with the fixture as written (`:819`) the `tool` row is inside the unit opened by the `user` message, so the assertion fails. Resolved by reordering the fixture to the leading-orphan shape (measured: `[user, assistant]`, `dropped == 1`). | Yes | 2026-10-24 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`, `REQ-006`, `REQ-007`, `REQ-008`
- **Source issue**: issues/done/20261021-093421_turn006_history-compression-reorders-and-duplicates-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-183637_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-061024
- **Related target files**: tests/agent/test_history_manager.py
