# Implementation Procedure: `scripts/agent/history_selection_policy.py`

## Goal

Replace the importance-sorted, value-equality selection in `select_turns_to_compress()` with whole-turn-unit
chronological selection, add the two grouping primitives, and delete the category machinery the new selection does
not use. Implements `REQ-001` (turn-unit primitive), `REQ-002` (group-atomic chronological selection), `REQ-003`
(`pinned` protection), `REQ-004` (position-based accounting), and `REQ-008` (delete the machinery the new selection
does not use) for this file.

## Scope

One file: `scripts/agent/history_selection_policy.py` (6054 B, 160 lines at baseline `a3c3ea3b6`).
- `SelectionResult` (`:18-24`) unchanged — its only readers are `scripts/agent/history.py:281` and `:384-386`.
- `classify_importance()` (`:65-93`) and `_POLICY_KEYWORDS` (`:27-31`) unchanged (`REQ-003`, `DR-004`).
- `select_turns_to_compress()`'s system/turn split (`:135-136`), the two counters (`:137-138`) and the guard
  (`:139-140`) stay exactly as written; `:142-156` is replaced.
- Delete `classify()` (`:44-63`), `partition_by_class()` (`:95-112`), `sort_by_importance()` (`:114-119`).
- Rewrite the module docstring (`:2-8`) and the body of the `HistorySelectionPolicy` class docstring (`:34-36`).

## Assumptions

- No production caller other than `scripts/agent/history.py` reads the deleted symbols: measured `grep -rn
  "partition_by_class|sort_by_importance" scripts/ tests/` → 13 references, all inside this file and
  `tests/agent/test_history_selection_policy.py` / `tests/agent/test_history_manager.py` (rows 3 and 4); `.classify(`
  → 6 references in the same three files. Blast radius is 3 files, below the `rules/toolchain.md` recording
  threshold.
- `tool_runner.py:242-246` makes tool results contiguous with their declaring assistant, so a `user`-delimited unit
  never splits a tool round (`REQ-001`).
- Nothing sets `pinned` on a conversation message today; `pinned` is read only at `:71` (`UNK-03` / `WI-004` is a
  separate decision). The unit rule is written anyway because `REQ-003` states it.

## Design decisions

- **Unit membership is decided by unit index, never by message value** (`REQ-004`). The current
  `m not in list` filters at `:146-156` silently drop duplicate-content messages (measured: 16 in, 14 accounted);
  index-based membership makes `len(system_msgs) + len(to_compress) + len(remaining) == len(history)` structural.
- **Protect boundary rounds outward and the compress loop breaks before adding a unit**, so `n_compress` becomes a
  floor and the last accepted unit may overshoot by at most its own size (`DR-001`). Overshoot is bounded by one
  unit, so `compressed_count` can exceed `compress_turns * 2` — soft-limit behavior, already the contract of
  `_fallback_truncate()`.
- **`group_importance()` is `max(..., default=0.0)`**, not a mean (`DR-003`): a unit that contains one high-scoring
  message must not be dropped as if it were low-importance. `default` keeps an empty sequence from raising
  `ValueError` even though the grouping primitive cannot produce one.
- **Both primitives are public `@staticmethod`s on `HistorySelectionPolicy`.** `tools/generate_reference_table.py`
  (`_extract_public_top_level_symbols`, `:214-235`) lists module-level functions and classes only, so no row is
  added to `docs/23_agent/agent_13_reference-api-generated.md`; `history.py` keeps reaching the policy through one
  collaborator (`self._selection_policy`).

## Alternatives considered

- **Re-tune the existing sort direction** (make `sort_by_importance()` ascending). Rejected by `DR-001`: the defect
  is that selection is value-equality filtered and category-bucketed at all; the `factual` bucket is unreachable
  (`turn006_probe1.out`, `factual is empty: True`), so the four-category model would stay in the code.
- **Keep `partition_by_class()` / `sort_by_importance()` as unused utilities.** Rejected by `DR-004`: measured zero
  callers after the rewrite, and `docs/23_agent/agent_04_02_...:40-44` documents a partition that never happens.
- **A module-level `group_turn_messages()` function.** Rejected: it would add a row to the generated API table
  (`agent_13`) and split policy ownership across two shapes for no gain.

## Implementation
### Target file

`scripts/agent/history_selection_policy.py`

### Procedure

1. Add `from collections.abc import Sequence` to the import block (`:10-15`). No other import changes.
2. Add `group_turn_messages()` (new) and `group_importance()` (new) as `@staticmethod`s in place of the deleted
   `partition_by_class()` (`:95-112`) and `sort_by_importance()` (`:114-119`), i.e. after `classify_importance()`:

   ```python
   @staticmethod
   def group_turn_messages(turn_msgs: Sequence[LLMMessage]) -> list[list[LLMMessage]]:
       """Split turn messages into chronological turn units.

       A unit opens at a user message and absorbs every assistant and tool message
       until the next user message. Messages before the first user message form the
       leading unit, so an orphan tool row is a unit of its own. Concatenating the
       units reproduces turn_msgs exactly.
       """
       units: list[list[LLMMessage]] = []
       for msg in turn_msgs:
           if msg.get("role") == "user" or not units:
               units.append([msg])
           else:
               units[-1].append(msg)
       return units

   @staticmethod
   def group_importance(unit: Sequence[LLMMessage]) -> float:
       """Score a turn unit by its most important member."""
       return max((HistorySelectionPolicy.classify_importance(m) for m in unit), default=0.0)
   ```

   `group_importance()` is the only remaining production caller of `classify_importance()`; `group_turn_messages()`
   is reached from `scripts/agent/history.py` through `self._selection_policy` (row 2).
3. Rewrite the body of `select_turns_to_compress()` from `:142` to `:156` to the unit algorithm (the split,
   counters, and guard at `:135-140` and the docstring's system-split note at `:129-135` stay):

   ```python
   units = self.group_turn_messages(turn_msgs)

   protect_from = len(units)
   tail = 0
   for i in range(len(units) - 1, -1, -1):
       if tail >= n_protect:
           break
       tail += len(units[i])
       protect_from = i

   window: list[int] = []
   taken = 0
   for i in range(protect_from):
       if taken >= n_compress:
           break
       if any(m.get("pinned") for m in units[i]):
           continue
       window.append(i)
       taken += len(units[i])
   if not window:
       return None

   to_compress: list[LLMMessage] = []
   remaining: list[LLMMessage] = []
   for i, unit in enumerate(units):
       if i in window:
           to_compress.extend(unit)
       else:
           remaining.extend(unit)
   return SelectionResult(system_msgs=system_msgs, to_compress=to_compress, remaining=remaining)
   ```

   `protect_from = len(units)` makes `n_protect == 0` protect nothing; a pinned unit is skipped and stays in
   `remaining` in place (`REQ-003`); `if not window: return None` is the `REQ-002` "nothing selectable without
   splitting a unit" path (its user-visible consequence is `UNK-02` / `WI-002`, out of scope here).
4. Delete `classify()` (`:44-63`), `partition_by_class()` (`:95-112`) and `sort_by_importance()` (`:114-119`),
   including their decorators (`:44`, `:95`, `:114`).
5. Rewrite the module docstring (`:2-8`) and the body of the class docstring (`:34-36`) to the unit contract:
   chronological whole-unit selection, oldest-first compression, importance used only for fallback ordering.
   **The first line of the class docstring stays byte-identical** — `docs/23_agent/agent_13_reference-api-generated.md`
   quotes it (`:82-85`) and that file is in the Plan's Forbidden edit scope (`UNK-06`, closed 2026-10-24).

### Method

Edit in place, in the order above (primitives, then selection body, then deletions, then docstrings) so the file
stays importable at every intermediate point. Confirm with `git diff` that `SelectionResult`, `classify_importance`,
`_POLICY_KEYWORDS`, `__init__`, and `select_turns_to_compress`'s `:135-140` region are unchanged. Run
`uv run python -m compileall -q scripts/` and `rg -n 'classify\(|partition_by_class|sort_by_importance' scripts/`
(only the policy file's own deleted definitions should disappear).

### Details

- `group_turn_messages()` never returns an empty unit, and never emits a unit for system-role messages: they are
  split off at `:135` before this call.
- Non-`user` messages before the first `user` message (a leading orphan `tool` row, a resumed-session shape) form
  the leading unit, so `AC-1`'s "reproduces its input" property holds for those inputs too.
- `any(m.get("pinned") for m in units[i])` is the `pinned` test; the `inf` value `classify_importance()` gives a
  pinned message is not used by selection at all.
- `to_compress` and `remaining` are both chronological because both are built by iterating `units` in index order.
- `taken >= n_compress` is checked before adding a unit, so a selection stops as soon as the floor is met;
  `len(to_compress) >= n_compress` holds whenever `window` is non-empty and no unit was skipped.

## Compatibility considerations

- `SelectionResult`'s three field names are unchanged, so `scripts/agent/history.py:281` and `:384-386` need no
  change for this row (row 2 changes their surrounding call sites for other reasons).
- `compressed_count` may now exceed `compress_turns * 2` (unit overshoot); `protected_count` semantics change in row
  2, not here. No test asserts an exact real-compression `compressed_count` (`test_history_manager.py:648-649` and
  `test_history_manager_new.py:49` assert the no-op zeros only).
- No doc or generated-table reference names the deleted symbols (`grep -rn "partition_by_class|sort_by_importance"
  docs/` is empty), so this row does not touch `agent_13`; the chapter rewrite is row 5.

## Security considerations

N/A: no new input handling, no subprocess, no file or network access; the module only reads message dict keys it
already read (`role`, `pinned`, `importance`, content).

## Rollback considerations

N/A: revert the commit. The deletion is confined to one module and its tests are removed in the same Plan (row 3),
so a revert restores a self-consistent state.

## Validation plan

- Unit (`T-1`, authored in row 3 before this row lands): `uv run pytest tests/agent/test_history_selection_policy.py -v`
  — grouping round-containment, leading non-`user` messages, orphan `tool` rows, chronology (`AC-2`), pinned
  exclusion (`AC-3`), identical-content accounting (`AC-4`), and the `None` case.
- Unchanged witnesses (`T-6`): `uv run pytest tests/agent/test_history_compression_consistency.py
  tests/agent/test_history_manager_new.py tests/agent/test_regression_history_compress_reload.py
  tests/integration/test_orchestrator_integration.py -q` must stay green.
- Static gates (`rules/toolchain.md`): `uv run ruff format scripts/`, `uv run ruff check scripts/`,
  `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run radon cc scripts/ -s -n C` (must no longer report
  `select_turns_to_compress`), `uv run python tools/check_module_size.py`, and
  `uv run python tools/generate_reference_table.py --type agent --check` (must report no drift).

## Completion criteria

- `group_turn_messages()` and `group_importance()` exist as `@staticmethod`s and satisfy `AC-1` for inputs
  containing tool rounds, a leading non-`user` message, and an orphan `tool` row.
- `select_turns_to_compress()` returns `to_compress` and `remaining` in chronological order, never places a unit
  containing a `pinned` message in `to_compress`, returns `None` when no whole unit is selectable, and accounts for
  every input message (`AC-2`, `AC-3`, `AC-4`).
- `classify()`, `partition_by_class()` and `sort_by_importance()` are gone, no reference to them remains in
  `scripts/`, and the two rewritten docstrings describe the unit contract with the class docstring's first line
  unchanged (`AC-8`).

## Out of Scope

- `scripts/agent/history.py` (row 2): the summary replacement, the unit-aware fallback, and the counters.
- The test file changes (`T-1`, `T-3`) are row 3, and `test_history_manager.py` changes are row 4.
- Making `/compact` agree with a `None` selection (`WI-002`, `UNK-02`) and deciding whether anything may set
  `pinned` (`WI-004`, `UNK-03`).
- Any change to `docs/23_agent/agent_13_reference-api-generated.md` (Forbidden edit scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `Sequence` import, `group_turn_messages()`, `group_importance()`; rewrite `select_turns_to_compress()`; delete `classify()`, `partition_by_class()`, `sort_by_importance()`; rewrite docstrings | Completed | 20261024-223813 | 20261024-223813 | Implemented in commit ed80d2154; verified vs current source + plan; archived per memo3.md |
| 2 | Add or update tests per Validation plan | Completed | 20261024-223813 | 20261024-223813 | Authored in row 3, green (24 passed) in commit ed80d2154; verified vs current source + plan; archived per memo3.md |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261024-223813 | 20261024-223813 | All gates green in commit ed80d2154; verified vs current source + plan; archived per memo3.md |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261024-223813 | 20261024-223813 | Chapter rewrite is row 5; `agent_13` untouched; archived per memo3.md |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | `UNK-06` (class docstring vs. the generated `agent_13` row) | N/A: closed by the owner 2026-10-24 — first docstring line stays unchanged | 2026-10-24 |

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
- **Related target files**: scripts/agent/history_selection_policy.py
