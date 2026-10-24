# Implementation Procedure: `scripts/agent/history.py`

## Goal

Make the compression path produce exactly one `[Conversation summary]` message that replaces the previous one, make
the fallback unit-atomic, and report the size of the summary block it produced. Implements `REQ-005` (exactly one
summary message), `REQ-006` (group-atomic fallback), `REQ-007` (reported counters), and `REQ-008`'s `history.py`
half (delete `_DEFAULT_PROTECT_IMPORTANCE`, rewrite the class docstring).

## Scope

One file: `scripts/agent/history.py` (15810 B, 407 lines at HEAD `2c2bbcce9`). Two plan steps land in this one
document (step 3, then step 5):
- step 3: `_SUMMARY_PREFIX` (new) constant, `_split_system_msgs()` (new), `_get_summary_text()` signature,
  `_build_summary_msg()`, `compress()`'s call sequence, `_build_compressed_result()`, `CompressResult.summary_chars`,
  `protected_count`, INFO/WARNING reporting.
- step 5: `_build_protected_ids()` and `_fallback_truncate()` unit-awareness, delete `_DEFAULT_PROTECT_IMPORTANCE`
  (`:32`), rewrite the `HistoryManager` class docstring (`:50-58`).
- `_call_compress_llm()` (`:202-229`), its prompt text (`:207-210`), `_build_history_text()`'s 300-character
  per-message cap (`:231-235`), `_is_over_char_limit()` (`:293-295`), `_check_limits()` (`:346-353`),
  `_log_skip_warning()` (`:355-370`), `count_chars()` (`:146-156`), `apply_config()` (`:106-125`) and
  `force_compress()` (`:127-145`) are unchanged.

## Assumptions

- The Plan's Forbidden edit scope keeps `cmd_config_stats.py`, `session_persister.py`, `context_view.py`,
  `conversation_state_manager.py`, `message_schema.py`, `shared/token_estimation.py` and `config/agent.toml`
  untouched; this row changes none of them.
- `CompressResult` is always constructed with keyword arguments — measured sites: `history.py:270-272`, `:285-290`,
  `:325-330`, `tests/integration/test_orchestrator_integration.py:50,417,433`,
  `tests/agent/test_orchestrator.py:66,1289,1304,1319,1348` — so a trailing defaulted field is safe (`REQ-007`).
- `_build_summary_msg()` has exactly one call site (`:392`) and no test calls it directly, so dropping its
  `system_msgs` parameter is safe.
- `history_protect_turns = 3` (`config/agent.toml:66`; default 2 at `config_section_builders.py:157-158`) means the
  newest units are always in `protected_ids`, so the empty-history floor computed below is unreachable in production.

## Design decisions

- **The previous summary is fed to the model, not concatenated by code** (`DR-002`): `_split_system_msgs()` removes
  every prior summary row and `_get_summary_text()` prepends a `PREVIOUS SUMMARY:` block to the transcript, outside
  the per-message cap at `:231-235`. Exactly one summary row follows from the pair of changes rather than from a
  post-hoc dedup pass.
- **`_SUMMARY_PREFIX` (new) becomes the single definition** of "what counts as a summary message": the inline literals at
  `:251` and `:258` disappear with `_build_summary_msg()`'s rewrite, and the literal at `:243` disappears with its
  docstring. `REQ-005`'s "removes a module-level duplicate-literal pair" is a correction, not an instruction — see
  the Plan's `Corrections from re-measurement`: no module-level constant exists today.
- **Fallback drops whole units sorted ascending by `group_importance()`** (`DR-003`), replacing the
  `HistorySelectionPolicy.classify_importance` sort key at `:306-309`. `sorted()` is stable, so equal-importance
  units drop oldest-first, which is why the plain `user`/`assistant` fixtures in
  `tests/agent/test_history_compression_consistency.py` still reduce in input order.
- **A whole-unit drop is skipped when it would leave fewer than 1 message** — stated explicitly because unit
  atomicity turns the existing `len(new_history) <= 1` guard at `:312` into a post-drop test. Keeping the newest
  message and reporting the soft-limit WARNING is safer than returning an empty history, which unit atomicity could
  otherwise produce by dropping a 3-message unit whole.
- **`summary_chars` (new) is data, not a gate** (`REQ-007`): INFO plus a conditional WARNING, no truncation, no new config
  key, no threshold constant. `/stats` surfacing stays `WI-005` (`cmd_config_stats.py` is Forbidden scope).

## Alternatives considered

- **Deduplicate summary rows in `_build_compressed_result()`** (keep appending, then collapse). Rejected: it keeps
  two definitions of a summary message and still sends the model a transcript whose old summary was never condensed.
- **Apply the 300-character cap to the prior-summary block too.** Rejected: the block would be cut mid-sentence and
  the model would receive a truncated summary of its own prior state; reviewing the cap itself is `WI-003`/`UNK-05`.
- **Mean instead of max for unit importance.** Rejected by `DR-003`: a unit holding one high-value message would be
  dropped because its neighbors are cheap.

## Implementation
### Target file

`scripts/agent/history.py`

### Procedure

Land step 3 first, then step 5; both are in this file, and step 5 depends on the grouping primitive added in row 1.

1. Add `from agent.history_selection_policy import HistorySelectionPolicy` to the existing import block at `:24-28`
   if it is not already imported by name (today the block imports the symbols the deleted sort key used; row 1 keeps
   `HistorySelectionPolicy` as the collaborator class).
2. Add the module constant next to the other module-level constants, replacing `_DEFAULT_PROTECT_IMPORTANCE` (`:32`):

   ```python
   _SUMMARY_PREFIX = "[Conversation summary]"
   ```

3. Add `_split_system_msgs()` (new) as a private method near `_build_history_text()` (`:231`):

   ```python
   def _split_system_msgs(
       self, system_msgs: list[LLMMessage]
   ) -> tuple[list[LLMMessage], list[str]]:
       """Split system messages into preserved rows and prior summary texts.

       Summary rows (content starting with _SUMMARY_PREFIX) are removed from the
       returned history and handed back as texts in input order, so several legacy
       summary rows collapse into one condensed block for the model.
       """
       preserved: list[LLMMessage] = []
       prior: list[str] = []
       for msg in system_msgs:
           content = str(msg.get("content") or "")
           if content.startswith(_SUMMARY_PREFIX):
               prior.append(content)
           else:
               preserved.append(msg)
       return preserved, prior
   ```

4. Change `_get_summary_text()` (`:372-378`) to
   `_get_summary_text(self, to_compress: list[LLMMessage], prior_summaries: list[str]) -> str | None`: when
   `prior_summaries` (new) is non-empty, pass `f"PREVIOUS SUMMARY:\n{'\n\n'.join(prior_summaries)}\n\n" +
   self._build_history_text(to_compress)` to `_call_compress_llm()`; otherwise keep the current single-argument
   call. `_call_compress_llm()` and its prompt are not edited.
5. Rewrite `_build_summary_msg()` (`:237-259`): keep `@staticmethod`, drop the `system_msgs` parameter and the
   append branch, and return `{"role": "system", "content": f"{_SUMMARY_PREFIX}\n{summary_text}"}` with a
   one-paragraph docstring.
6. Update `compress()` (`:261-291`): after `split = self._selection_policy.select_turns_to_compress(history)`
   (`:277`) add `preserved_system, prior_summaries = self._split_system_msgs(split.system_msgs)`, pass
   `prior_summaries` (new) at `:281`, and pass `preserved_system` (new) to `_build_compressed_result()` at `:291`. The
   no-op return at `:270-272`, the fallback branch at `:284`, and the error branch at `:285-290` keep their shape.
7. Append `summary_chars: int = 0` as the last field of `CompressResult` (`:39-47`).
8. Update `_build_compressed_result()` (`:380-398`): take `preserved_system` (new), build
   `summary_msg = self._build_summary_msg(summary_text)`, compute
   `summary_chars = len(str(summary_msg["content"]))`, set `protected = len(remaining)` (replacing
   `len(remaining) - len(system_msgs)` at `:387`), log
   `logger.info("History compressed: %d messages summarized, summary_chars=%d", n, summary_chars)`, warn when
   `summary_chars >= self.count_chars(split.to_compress)`, and return
   `preserved_system + [summary_msg] + remaining` at `:398`. Pass `summary_chars` (new) into the returned
   `CompressResult`.
9. (step 5) Rewrite `_build_protected_ids()` (`:332-339`): keep the system-role ids (`:335`) and replace the
   `turn_msgs[-n_protect:]` slice (`:337-338`) with the same outward-rounding tail run the selector uses — walk
   `self._selection_policy.group_turn_messages(turn_msgs)` from the end until `>= n_protect` messages are covered
   and add every member of each covered unit.
10. (step 5) Rewrite `_fallback_truncate()` (`:297-330`): build candidates as whole units that contain no protected
   id, `sorted(units, key=self._selection_policy.group_importance)` ascending, and drop one whole unit per
   iteration while `self._is_over_char_limit(new_history)` and the drop leaves at least one message in
   `new_history` (post-drop test). Keep the counter at `:316`, the message-count accounting at `:317`, the
   soft-limit WARNING at `:318-323`, and
   `CompressResult(compressed_count=dropped, protected_count=len(protected_ids), summary_added=False,
   is_fallback=True)` at `:325-330` with `summary_chars` (new) left at its default 0.
11. (step 5) Rewrite the `HistoryManager` class docstring (`:50-58`) to the new contract (chronological
   whole-unit selection, one summary message, unit-atomic fallback). Delete `_DEFAULT_PROTECT_IMPORTANCE` (`:32`);
   `rg -n "_DEFAULT_PROTECT_IMPORTANCE" scripts/ tests/` must then be empty.

### Method

Edit in place, step 3 items 1-8 first and run `uv run pytest tests/agent/test_history_manager.py
tests/agent/test_history_compression_consistency.py -q` before starting step 5 items 9-11, so a fallback regression
is attributable to its own commit. Confirm with `git diff` that `force_compress()`, `_check_limits()`,
`_call_compress_llm()`, `_is_over_char_limit()`, `count_chars()` and `_build_history_text()` are byte-identical.
Then `rg -n "classify_importance" scripts/agent/history.py` must be empty and `rg -n "Conversation summary"
scripts/agent/history.py` must show only `_SUMMARY_PREFIX` (new)'s definition.

### Details

- The WARNING condition is `summary_chars >= self.count_chars(split.to_compress)`: `count_chars()` (`:146-156`)
  counts content plus serialised `tool_calls`, so both sides are measured the same way. This is exactly the shape of
  `turn006_probe2.out`'s 1296-character block — with the `:231-235` cap a two-turn slice yields at most about 1200
  characters of transcript, so a 1296-character block cannot be smaller than what it replaced.
- Use `self._warn_once` (`:93`, `shared.token_counter._WarnOnce`) if the WARNING must not repeat every turn; the
  Plan does not require it, so logging plainly is acceptable.
- `summary_chars` (new) measures the whole block including the `_SUMMARY_PREFIX` (new) header, because that is the text
  occupying the context window (`REQ-007`).
- After step 5 the only production caller of `classify_importance()` is `group_importance()` inside
  `scripts/agent/history_selection_policy.py` (row 1).
- A `tool` message whose declaring assistant is protected can no longer be dropped, and a dropped unit never leaves
  an orphan `tool` row — that is `AC-6` and the end of the `turn006_probe3c.out` shape.

## Compatibility considerations

- `CompressResult` keeps its existing field names and adds one trailing defaulted field, so
  `cmd_config_stats.py:84-87`, `session_persister.py:136-138`, `tests/agent/test_orchestrator.py` and
  `tests/integration/test_orchestrator_integration.py` need no change (`T-6`).
- `protected_count` becomes `len(remaining)` on the compression path and stays `len(protected_ids)` on the fallback
  path. Measured: no test asserts an exact real-compression `protected_count`; `test_history_manager.py:648-649` and
  `test_history_manager_new.py:49` assert the no-op zeros, which stay 0.
- The `[Conversation summary]` prefix, the `role="system"` shape and the prompt wording are unchanged, so
  `tests/agent/test_session_message_repo.py:478-543` and `tests/agent/test_orchestrator.py:1286` fixtures keep
  working.
- `compressed_count` on the compression path may exceed `compress_turns * 2` (row 1's unit overshoot); the fallback's
  `compressed_count` stays a message count.

## Security considerations

N/A: no new external input, no subprocess, no file or network access. The prior-summary block is built from
messages already in the history and is sent to the same summarization endpoint through the unchanged
`_call_compress_llm()`; redaction stays with `scripts/shared/logger.py`'s `_RedactionFilter`.

## Rollback considerations

Revert in two commits if the Plan's phases are landed separately: reverting step 5 restores per-message fallback
deletion without touching the summary contract, and reverting step 3 restores summary accumulation. `git checkout`
against this single path is sufficient for either half.

## Validation plan

- Unit (`T-2`, `T-4`, `T-5`, authored in row 4): `uv run pytest tests/agent/test_history_manager.py -v` — one summary
  message after three `force_compress()` cycles, no verbatim carry-over, bounded total length, legacy two-row input
  collapsing to one, `summary_chars` (new) equality and guard, `protected_count == retained turn messages`, and the
  fallback unit-atomicity assertions.
- Unchanged witnesses (`T-6`): `uv run pytest tests/agent/test_history_compression_consistency.py
  tests/agent/test_history_manager_new.py tests/agent/test_regression_history_compress_reload.py
  tests/integration/test_orchestrator_integration.py -q`. Six-file baseline measured 2026-10-24 with the Plan's exact
  command: `139 passed`.
- Static gates (`T-7`, `rules/toolchain.md`): `uv run ruff format scripts/`, `uv run ruff check scripts/`,
  `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run radon cc scripts/ -s -n C`,
  `uv run python tools/check_module_size.py` (15810 B against a 20480 B baseline-gated gate).
- Full suite (`T-8`): `uv run pytest tests/ -x -q` then `uv run pytest`. The Plan's `9938 passed / 9 skipped`
  baseline is not current — re-run rather than compare against it.

## Completion criteria

- A compressed history contains exactly one `[Conversation summary]` message, including inputs that already held
  two summary rows, and the prior summary text is not carried over verbatim (`AC-5`).
- `CompressResult.summary_chars` equals the summary message's content length, the INFO line names it, the WARNING
  fires when `summary_chars >= count_chars(to_compress)`, and `protected_count` equals the number of retained turn
  messages (`AC-7`).
- The fallback never drops part of a turn unit, never leaves an orphan `tool` row, and never returns an empty
  history (`AC-6`).
- `_DEFAULT_PROTECT_IMPORTANCE` and the inline `[Conversation summary]` literals are gone, and the class docstring
  states the unit contract (`AC-8`).

## Out of Scope

- `scripts/agent/history_selection_policy.py` (row 1) and the two test files (rows 3 and 4).
- `cmd_config_stats.py` / `session_persister.py` changes and `/stats` surfacing of `summary_chars` (new) (`WI-005`).
- The 300-character per-message cap itself (`WI-003`, `UNK-05`) and the token-source decision (`WI-001`, `UNK-01`).
- An absolute ceiling on summary size: the issue's acceptance criteria 2 and 3 are not closed by this Plan and stay
  gated on `WI-003` and `UNK-04`.

## Adversarial verification findings

Adversarial verification of this row against current source (`rg`/Read plus the
`radon cc scripts/ -s -n C` AC-10 gate) found and corrected the items below before
archival. Each is recorded here so the archive reflects what actually shipped.

- **Refactor left a stray closing paren (`history.py:362`).** Dropping `_fallback_truncate`
  below the C threshold required factoring its body into two private `@staticmethod`s:
  `_drop_candidate_units()` (whole units with no protected member, lowest importance first)
  and `_apply_unit_drops()` (drops whole candidate units while over the char limit, never
  emptying the history). The first edit of that refactor left a dangling `)` immediately
  after `_apply_unit_drops()`'s `return new_history`, which made the file fail to parse.
  Removed the stray paren; the file parses and `uv run pytest tests/agent/test_history_manager.py`
  is green. This is a net-new method, not a Plan instruction — the Plan's `Corrections from
  re-measurement` covers literal/constant drift, not a refactor artifact.
- **AC-10 complexity gate.** After the refactor, `radon cc scripts/ -s -n C` reports neither
  `history.py` nor `select_turns_to_compress` (the selector's method is unchanged from row 1).
  `classify_importance()` stays C(14) and is disclosed here rather than hidden; only
  `_fallback_truncate`'s extracted helpers were refactored to clear the gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | step 3: `_SUMMARY_PREFIX` (new), `_split_system_msgs()`, `_get_summary_text()`, `_build_summary_msg()`, `compress()`, `_build_compressed_result()`, `CompressResult.summary_chars`, counters and logs | Completed | 20261024-230000 | 20261024-231000 | Plan step 3 (Phase 2); row 1 landed first |
| 2 | step 5: unit-aware `_build_protected_ids()` and `_fallback_truncate()`, delete `_DEFAULT_PROTECT_IMPORTANCE`, class docstring | Completed | 20261024-231000 | 20261024-232000 | Refactored into `_drop_candidate_units()` + `_apply_unit_drops()` to clear AC-10; removed a stray paren left by the refactor (`:362`) |
| 3 | Add or update tests per Validation plan | Completed | — | — | Tests are authored in row 4 (Plan steps 4 and 6) |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261024-232000 | 20261024-233000 | ruff, mypy (440 files), lint-imports, bandit, radon `-n C` (neither target reported), check_module_size, check_compat_shims, generate_reference_table --check, check_docstrings; T-6 witnesses + T-8 full suite (10024 passed / 12 skipped) |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: chapter rewrite is row 5 (out of scope for this row) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no open blocker for this row | N/A: the absolute summary-size ceiling is out of scope (`UNK-04`, `WI-003`), not a blocker here | — |

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
- **Related target files**: scripts/agent/history.py
