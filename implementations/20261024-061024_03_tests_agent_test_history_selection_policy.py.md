# Implementation Procedure: `tests/agent/test_history_selection_policy.py`

## Goal

Replace the tests that assert the deleted classification/sorting API with tests that assert the turn-unit contract:
chronological whole-unit selection, unit atomicity across the partition boundary, `pinned` protection by unit, and
position-based accounting. Implements `REQ-001`..`REQ-004` as a failing specification and `REQ-008`'s test half
(delete `TestPartitionByClass` and `TestSortByImportance`). This is Plan step 1 (Phase 1), so the file is authored
**before** `scripts/agent/history_selection_policy.py` (row 1, Plan step 2) changes.

## Scope

One file: `tests/agent/test_history_selection_policy.py` (7910 B, 210 lines, 13 test functions at HEAD `2c2bbcce9`).

- Delete 7 tests: the `# ── partition_by_class() ──` banner (`:31`) with `TestPartitionByClass` (`:34-81`, 3 tests) and
  the `# ── sort_by_importance() ──` banner (`:84`) with `TestSortByImportance` (`:87-114`, 4 tests). Deleting `:31-116`
  removes both blocks; the `# ── select_turns_to_compress() ──` banner at `:117` stays.
- Keep unchanged: the module docstring's file-name line, the `_msg()` helper (`:12-28`), and
  `TestSelectTurnsToCompress` (`:120-210`, 6 tests).
- Add 18 tests in 6 new classes (`T-1`).
- Imports (`:6-9`), `_msg()`'s signature, and `HistorySelectionPolicy`'s constructor call shape are unchanged.

## Assumptions

- `classify_importance()` (`history_selection_policy.py:65-93`) stays public and unchanged (`REQ-003`, `DR-004`), so the
  new tests may assert its measured scores: `pinned` → `inf`, explicit `importance` → that value, `system` → 1.0, `tool`
  with `error`/`failed` in the content → 0.8, plain `tool` → 0.3, assistant with a policy keyword → 0.8, `user` with a
  policy keyword → 0.9, assistant with `tool_calls` (no keyword) → 0.6, everything else → 0.5.
  `_POLICY_KEYWORDS` (`:26-28`) matches `rule|policy|always|never|constraint|must|forbidden|required|invariant`.
- The retained guard `len(turn_msgs) < n_compress + n_protect` (`:139-140`) stays, per `REQ-002` and row 1; every
  "nothing selectable" test below is written so the `None` it asserts comes from unit selection or the guard, and the
  fixture states which.
- The Plan's `Corrections from re-measurement` (`plans/20261023-183637_plan.md:813-830`) is authoritative for counts:
  the frozen table's "`:34-118` (13 tests total)" means 13 in the whole file, 7 inside the deleted range.
- Ruff is the only static gate that touches this file: `[tool.mypy] files = ["scripts/"]` excludes tests, and
  `[tool.ruff.lint]` selects the default rule set (no ARG), so `_msg()`'s optional keyword arguments are not
  findings.

## Design decisions

- **Author the tests red, before the code** (Plan Phase 1 order, `plans/20261023-183637_plan.md:502-503`): all 18 added
  tests fail against the current `select_turns_to_compress()` — 9 with `AttributeError` (`group_turn_messages()` /
  `group_importance()` do not exist yet) and 9 with an assertion that names the split-round or the descending sort the
  Plan removes. That is the Plan's stated `Output` for step 1: "a failing specification of `REQ-001`..`REQ-004`".
- **Fixtures are chosen so old and new behavior differ** (measured with `/tmp/opencode/verify_row3_fixtures.py`): a
  history of uniform-0.5 `user`/`assistant` pairs is accidentally chronological under the current descending sort
  (`sort_by_importance` is stable), so every chronology test places a 0.9 policy-keyword `user` message in a unit that
  is *selectable but not oldest* (`compress_turns=2`, `protect_turns=1`, keyword at input index 4). Current code
  selects `[4, 0, 1, 2]`; the unit algorithm selects `[0, 1, 2, 3]`.
- **Unit identity is asserted by input index, not by value** (`REQ-004`): each selection test builds
  `pos = {id(m): i for i, m in enumerate(history)}` and asserts the index sequences of `to_compress` and `remaining`.
  Value comparison would hide the duplicate-content defect `turn006_probe1.out` reports.
- **`pinned` is tested as a unit property, not a score** (`REQ-003`, `AC-3`): the assertions check that the pinned unit
  is in `remaining` and that an all-pinned candidate set returns `None`. The `inf` score itself stays covered by
  `TestClassifyImportance` in `tests/agent/test_history_manager.py`, which this row does not touch.
- **One module-level `_TOOL_CALLS` (new) constant** instead of repeating the inline `tool_calls` literal (`:38-45`, `:93-100`)
  that the deleted classes carried, because 4 of the new fixtures need an assistant-with-`tool_calls` message.

## Alternatives considered

- **Keep `TestPartitionByClass`/`TestSortByImportance` and mark them skipped.** Rejected by `REQ-008` and `AC-8`:
  `grep -rn "partition_by_class\|sort_by_importance" scripts/ tests/` must return nothing, and a skipped test still
  names the deleted API.
- **Assert exact `to_compress` lengths (`== compress_turns * 2`).** Rejected: `REQ-002`'s last-unit overshoot makes the
  length `>= n_compress`, so an exact-length assertion would forbid the overshoot the Plan requires. The overshoot is
  asserted directly instead (`test_last_unit_may_overshoot_the_compress_target` (new)).
- **Rewrite the 6 retained tests into the new classes.** Rejected: each passes unchanged under the unit algorithm
  (per-test re-derivation in Validation plan), and rewriting passing guard/system-split tests adds churn with no
  coverage gain.
- **Add a `pytest.raises(AttributeError)` shim test for the new methods before they exist.** Rejected: it locks in the
  wrong contract for the commit that lands row 1, and the red run is the specification the Plan asks for.

## Implementation
### Target file

`tests/agent/test_history_selection_policy.py`

### Procedure

1. Rewrite the module docstring (`:2-3`): keep the file-name line, replace "Unit tests for HistorySelectionPolicy —
   pure classification/sorting logic." with the unit contract (turn-unit grouping, chronological whole-unit
   selection, position-based accounting).
2. Add after `_msg()` (`:28`):

   ```python
   _TOOL_CALLS = [
       {"id": "x", "type": "function", "function": {"name": "f", "arguments": "{}"}}
   ]
   ```

3. Delete `:31-116`: the `# ── partition_by_class() ──` banner, `TestPartitionByClass` (`:34-81`), the
   `# ── sort_by_importance() ──` banner, `TestSortByImportance` (`:87-114`), and the blank separator lines. The
   `# ── select_turns_to_compress() ──` banner (`:117`) and everything from `:120` stay byte-identical.
4. In the deleted position (directly after `_TOOL_CALLS` (new), before the `:117` banner) add the grouping sections:

   ```python
   # ── group_turn_messages() ──────────────────────────────────────────────────


   class TestGroupTurnMessages:
       ...  # 4 tests


   # ── group_importance() ─────────────────────────────────────────────────────


   class TestGroupImportance:
       ...  # 5 tests
   ```

   Fixtures and assertions (all measured):
   - `test_units_reproduce_their_input` (new) (`AC-1`): `msgs = [tool("orphan"), user("q1"), assistant(tool_calls=_TOOL_CALLS),
     tool("OK: done"), tool("OK: done2"), user("q2"), assistant("a2")]`; assert
     `[m for unit in group_turn_messages(msgs) for m in unit] == msgs` and `[len(u) for u in units] == [1, 4, 2]`.
   - `test_unit_absorbs_assistant_and_tool_rows` (new): the same fixture without the leading orphan → `[4, 2]`.
   - `test_leading_non_user_messages_form_a_leading_unit` (new): `[tool("orphan"), user, assistant]` → `[1, 2]` and
     `units[0][0] is msgs[0]`.
   - `test_consecutive_user_messages_open_their_own_units` (new): `[user("q1"), user("q2"), assistant("a2")]` → `[1, 2]`
     (`REQ-001`: every unit opens at a `user` message).
   - `test_group_score_is_the_max_member_score` (new) (`REQ-006`): `[assistant(tool_calls=_TOOL_CALLS)=0.6, tool("OK:
     done")=0.3]` → `group_importance(unit) == 0.6`.
   - `test_plain_pair_scores_half` (new): `[user("hello"), assistant("hi")]` → `0.5`.
   - `test_explicit_importance_participates_in_the_max` (new): `[user("x", importance=0.95), assistant("y")]` → `0.95`.
   - `test_pinned_member_makes_the_unit_infinite` (new): `[user("a"), user("b", pinned=True)]` → `float("inf")`.
   - `test_empty_group_scores_zero` (new): `HistorySelectionPolicy.group_importance([]) == 0.0` (row 1's `max(..., default=0.0)`).
5. Keep `TestSelectTurnsToCompress` (`:120-210`, 6 tests) byte-identical, and append after it (`:210`) the selection
   invariant sections:

   ```python
   # ── chronological whole-unit selection (REQ-002, REQ-004) ──────────────────


   class TestSelectionIsChronological:
       ...  # 3 tests


   class TestSelectionUnitAtomicity:
       ...  # 2 tests


   class TestPinnedUnitProtection:
       ...  # 2 tests


   class TestPositionBasedAccounting:
       ...  # 2 tests
   ```

   Fixtures and assertions (all measured against row 1's algorithm and against the current code):
   - Shared chronology fixture `_CHRONO` (new): 8 messages in 4 pairs whose unit-2 `user` content is
     `"You must always follow the rule"` (score 0.9); `compress_turns=2`, `protect_turns=1`.
   - `test_oldest_units_are_compressed_first` (new) (`AC-2`): assert the `to_compress` indices are `[0, 1, 2, 3]` and the 0.9
     message is in `remaining`. Current code yields `[4, 0, 1, 2]` (`sort_by_importance` at
     `history_selection_policy.py:114-119` + `compressible[:n_compress]` at `:152`).
   - `test_both_partitions_keep_input_index_order` (new) (`AC-2`, the `turn006_probe6.out` shape):
     `[user, assistant(tool_calls=_TOOL_CALLS)=0.6, tool("OK: done")=0.3, tool("OK: done2")=0.3, user, assistant]`,
     `compress_turns=2`, `protect_turns=0` → the index sequences are `to_compress [0, 1, 2, 3]` and `remaining [4, 5]`.
     Current code yields `to_compress [1, 0, 4, 5]`.
   - `test_protected_tail_is_the_newest_units` (new) (`REQ-002(a)`): `_CHRONO` (new) → `remaining` indices `[4, 5, 6, 7]`. Current
     code yields `[3, 5, 6, 7]` (the count-based tail splits unit 1).
   - `test_tool_round_never_splits_across_partitions` (new) (`AC-2`, `AC-6`'s selection half):
     `[user, assistant(tool_calls=_TOOL_CALLS), tool("OK: done"), tool("OK: done2"), user("You must always follow the
     rule"), assistant]`, `compress_turns=1`, `protect_turns=1` → `to_compress [0, 1, 2, 3]`, `remaining [4, 5]`, and
     `remaining` contains no `tool` row. Current code compresses `[1, 0]` and leaves the two `tool` rows at `:2, :3`
     orphaned in `remaining`.
   - `test_last_unit_may_overshoot_the_compress_target` (new) (`REQ-002(b)`):
     `[user, assistant(tool_calls=_TOOL_CALLS), tool("OK: done"), user, assistant]`, `compress_turns=1`
     (`n_compress=2`), `protect_turns=0` → `len(to_compress) == 3`, `len(remaining) == 2`. Current code: 2.
   - `test_pinned_unit_stays_in_remaining` (new) (`AC-3`):
     `[user(pinned=True), assistant, user, assistant, user, assistant]`, `compress_turns=2`, `protect_turns=0` →
     `to_compress [2, 3, 4, 5]`, `remaining [0, 1]`, neither pinned message in `to_compress`. Current code compresses
     `[0, 1, 2, 3]`.
   - `test_returns_none_when_every_candidate_unit_is_pinned` (new) (`REQ-002(d)`): `[user(pinned=True), assistant]`,
     `compress_turns=1`, `protect_turns=0` → passes the guard (`2 < 2` is false) and asserts `result is None`. Current
     code returns a split that compresses the pinned pair.
   - `test_every_message_is_accounted_for` (new) (`AC-4`, the `turn006_probe1.out` shape): 8 pairs (16 messages) whose unit-2 and
     unit-4 `user` contents are both `"same"`; `compress_turns=2`, `protect_turns=2` →
     `len(system_msgs) + len(to_compress) + len(remaining) == 16`, `to_compress [0, 1, 2, 3]`, `remaining [4 .. 15]`.
     Current code accounts 15.
   - `test_identical_content_messages_are_both_retained` (new) (`AC-4`): same fixture →
     `remaining.count({"role": "user", "content": "same"}) == 2`. Current code: 1.

### Method

Edit in place in the order above (docstring, `_TOOL_CALLS` (new), deletions, grouping sections, selection sections), then run

```bash
uv run pytest tests/agent/test_history_selection_policy.py -q
```

Expect `6 passed, 18 failed` with the current `scripts/agent/history_selection_policy.py`: 9 `AttributeError` on
`group_turn_messages()`/`group_importance()`, and 9 assertion failures whose diffs are the index sequences listed above.
Commit this file together with row 1 (Plan step 2) so `T-1` is green at the commit boundary (Plan `T-3`: "rewritten to
the unit semantics in the same commit as the code change"). Then re-run and expect `24 passed`. Format with
`uv run ruff format tests/agent/test_history_selection_policy.py` and
`uv run ruff check tests/agent/test_history_selection_policy.py`.

### Details

- Fixture sizes are chosen against the retained guard `len(turn_msgs) < n_compress + n_protect` (`:139-140`): every
  selection fixture except `test_returns_none_when_every_candidate_unit_is_pinned` (new) satisfies
  `len(turn_msgs) >= n_compress + n_protect`, so a `None` can only come from the unit window being empty.
- `_msg()` already supports `tool_calls`, `pinned`, and `importance` (`:12-28`), so no helper signature changes are
  needed; `_TOOL_CALLS` (new) only removes literal duplication.
- The deleted classes were the file's only `tool`-role fixtures (`:37`, `:41`, `:93`, `:100`); the new fixtures carry
  that surface, matching the Plan's `T-3` sweep (`plans/20261023-183637_plan.md:561-567`).
- Call the new primitives as `HistorySelectionPolicy.group_turn_messages(...)` /
  `HistorySelectionPolicy.group_importance(...)` — `@staticmethod`s on the class, the same call shape the deleted
  tests used (`:66`, `:89`). Do not import them as module-level names (row 1 adds no module-level function).
- `SelectionResult`'s field names (`system_msgs`, `to_compress`, `remaining`) are unchanged, so assertions read exactly
  as the retained tests' do.
- Use `is` identity for the leading-unit assertion (`units[0][0] is msgs[0]`); value equality would pass on a reordered
  copy.

## Compatibility considerations

- Only this file and `scripts/agent/history_selection_policy.py` reference `partition_by_class` or
  `sort_by_importance` (13 references measured across `history_selection_policy.py`,
  `tests/agent/test_history_selection_policy.py`, `tests/agent/test_history_manager.py`). This row removes the 7 test
  references; row 4's `TestClassify` deletion removes the `classify()` references, which is what makes `AC-8`'s grep
  empty.
- `tests/agent/test_history_manager.py:17` imports `_POLICY_KEYWORDS` and `HistorySelectionPolicy` for
  `TestClassifyImportance` (`:598-641`), which stays; this row changes nothing that file imports.
- `docs/23_agent/agent_13_reference-api-generated.md` is not regenerated by this row: the generator lists module-level
  classes and functions only (`tools/generate_reference_table.py:214-235`), and
  `classify()`/`partition_by_class()`/`sort_by_importance()` are class methods that never had rows.
- The Plan's `T-1` selector (`tests/agent/ -k "history or compress or token_counter or policy or selection or
  truncate or partition or importance or pinned"`) loses its `partition` matches; the selector stays valid, only its
  count changes. The recorded `74 passed` figure is a pre-change baseline, not a target.

## Security considerations

N/A: test-only change. No new subprocess, network, or file access; fixtures are in-memory dicts, and no secret or
personal data is introduced.

## Rollback considerations

`git checkout -- tests/agent/test_history_selection_policy.py` restores the pre-change file (single path, allowed by the
repository execution policy). Because Phase 1 lands this file and row 1 in one commit, reverting that commit restores
both the old tests and the old selection algorithm; reverting only this file leaves row 1's code without its
specification, which is why the two are not reverted independently.

## Validation plan

- Red specification (this row, before row 1): `uv run pytest tests/agent/test_history_selection_policy.py -q` →
  `6 passed, 18 failed` with the reasons listed in Method.
- Green (`T-1`, after row 1 lands): the same command → `24 passed`. Pre-change baseline for reference: 13 passed
  (`plans/20261023-183637_plan.md:299`).
- `T-3` sweep: the 6 retained tests need no edit, each re-derived against the unit algorithm —
  `test_returns_none_when_not_enough_turns` (`:121`, guard `2 < 4`),
  `test_returns_none_when_protect_consumes_all` (`:127`, guard `4 < 8`), and
  `test_returns_none_with_only_system_messages` (`:174`, guard `0 < 2`) stay `None` through the unchanged guard;
  `test_returns_split_with_system_msgs` (`:138`) and
  `test_protected_turns_excluded_from_compressible` (`:153`, `to_compress` = 2 messages) and
  `test_ephemeral_and_memory_injected_messages_never_compressible` (`:179`) stay satisfied by the unchanged system/turn
  split (`:135-136`).
- Witness (`T-6`): `uv run pytest tests/agent/test_history_manager.py
  tests/agent/test_history_compression_consistency.py tests/agent/test_history_manager_new.py
  tests/agent/test_regression_history_compress_reload.py tests/integration/test_orchestrator_integration.py -q`
  stays green with this row's deletions in place.
- Style: `uv run ruff format` / `uv run ruff check` on this file. mypy is out of scope
  (`[tool.mypy] files = ["scripts/"]`).

## Completion criteria

- `TestPartitionByClass` and `TestSortByImportance` are gone, and
  `grep -n "partition_by_class\|sort_by_importance" tests/agent/test_history_selection_policy.py` is empty (`AC-8`).
- `group_turn_messages()` has 4 passing tests covering round containment, a leading non-`user` message, consecutive
  `user` messages, and exact input reproduction (`AC-1`).
- `group_importance()` has 5 passing tests covering the max-member rule, a plain pair, an explicit `importance`, a
  `pinned` member, and the empty group (`REQ-006`'s sort key).
- Selection tests prove: both partitions are index-increasing, the protected tail is whole newest units, a `tool` round
  is never split across the partition, the last unit may overshoot `compress_turns * 2`, a pinned unit is never
  compressed, an all-pinned candidate set returns `None`, and all 16 messages of the duplicated-content fixture are
  accounted for (`AC-2`, `AC-3`, `AC-4`).
- `uv run pytest tests/agent/test_history_selection_policy.py -q` reports `24 passed` once row 1 lands.

## Out of Scope

- `scripts/agent/history_selection_policy.py` (row 1) — this row specifies it, it does not edit it.
- `tests/agent/test_history_manager.py` (row 4): `TestClassify`'s deletion, `test_drops_tool_messages_first`'s fixture
  change, `T-4` and `T-5`.
- Any change to `classify_importance()` scoring values, `_POLICY_KEYWORDS`, or `SelectionResult` (`REQ-003`).
- Live-model summary-size measurement (`tests/live/test_live_summarization_smoke.py`, `UNK-04`) and the 300-character
  per-message cap (`WI-003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the module docstring; add `_TOOL_CALLS` (new); delete `:31-116` (`TestPartitionByClass`, `TestSortByImportance`) | Pending | — | — | Plan step 1 (Phase 1), no code dependency |
| 2 | Add `TestGroupTurnMessages` (new) (4) and `TestGroupImportance` (new) (5) | Pending | — | — | Red until row 1 lands |
| 3 | Add the 4 selection-invariant classes (9 tests); keep `TestSelectTurnsToCompress` byte-identical | Pending | — | — | `AC-2`, `AC-3`, `AC-4` |
| 4 | Run the validation sequence (`rules/toolchain.md`): red run, then green with row 1, ruff, `T-6` witnesses | Pending | — | — | Commit with row 1 (`T-3`) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no open blocker for this row | N/A: `UNK-02` (a soft-limit history that never compresses) is a documented consequence, not a blocker here | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-008`
- **Source issue**: issues/done/20261021-093421_turn006_history-compression-reorders-and-duplicates-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-183637_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-061024
- **Related target files**: tests/agent/test_history_selection_policy.py
