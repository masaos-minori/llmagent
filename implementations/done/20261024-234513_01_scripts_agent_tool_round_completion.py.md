# Implementation Procedure: scripts/agent/tool_round_completion.py

## Goal

Replace the strict `call_order` map and the default-`0` sort in `complete_round()` with a private
positional merge helper, so a raw batch containing an entry without an `id` key completes without
`KeyError` and every persisted tool row keeps its declared batch position (`REQ-001` lenient batch
ordering, `REQ-002` distinct batch positions, `REQ-003` unmatched results appended last, `REQ-004`
empty `tool_call_id` preserved).

## Scope

- Modify `complete_round()` in `scripts/agent/tool_round_completion.py` (`:47-49` only) and add one
  private module-level helper.
- Every other statement of the completion step — `collect()`, `build_denied_messages()`,
  `pair_round_results()`, `extend_messages()`, `save_many()` — stays byte-identical.

## Assumptions

- `prepare_tool_calls()` returns its failure tuples in input order with `tool_call_id == ""` for
  id-less calls (`tool_preparation.py:75-84`, `TestPrepareToolCallsBatchOrdering`); this helper only
  re-orders the merged list, it does not mint ids (`REQ-004`).
- Denied ids never appear in `results` (they go through `build_denied_messages`), so the scan never
  needs to consume them.
- Batches are small (one assistant message), so a positional scan is cheap in the hot path.

## Design decisions

- Positional walk over the declared batch instead of an id-keyed map: a dict keyed by id cannot hold
  two positions for one id (`D-2`) and `.get(r[0], 0)` silently assigns position `0` to unmatched
  rows; lenient `tc.get("id") or ""` alone would fix `D-1` while leaving `D-2` in place (Plan Design,
  "Why positional, not id-keyed").
- The helper stays private and inside this module: the merge is the round owner's job
  (`tool_result_pairing.py` stays pairing-only, `UNK-04` resolution) and a pure function over
  `(tool_calls, results)` is directly unit-testable (test doc row 2).

## Alternatives considered

- Lenient key access only (`tc.get("id") or ""` in the map): rejected — keeps the duplicate-id
  collapse and puts id-less rows at position `0`.
- Moving the merge into `tool_result_pairing.py`: rejected — `UNK-04` resolved; that module's `seen`
  guard answers *unanswered* ids, not batch ordering.

## Implementation

### Target file

`scripts/agent/tool_round_completion.py`

### Procedure

1. Add a private module-level function `_merge_in_declared_order` (new) after the `RoundState`
   dataclass.
2. In `complete_round()`, replace lines `:47-49`
   (`call_order = {tc["id"]: i for i, tc in enumerate(tool_calls)}`,
   `results = [*state.collected.values(), *state.prep_failures]`,
   `results.sort(key=lambda r: call_order.get(r[0], 0))`) with the single merged-list construction
   shown under Method. Lines `:50-58` are untouched.

### Method

```python
def _merge_in_declared_order(
    tool_calls: list[dict],
    results: list[tuple],
) -> list[tuple]:
    """Merge collected results and preparation failures into declared batch order.

    Each entry of `tool_calls` consumes, in order, the earliest not-yet-consumed
    result whose `tool_call_id` equals the entry's id; an absent or empty id is
    treated as `""`. Results consumed by no entry are appended last, in their
    original relative order. Ids are never indexed strictly.
    """
    remaining = list(results)
    merged: list[tuple] = []
    for tc in tool_calls:
        tc_id = tc.get("id") or ""
        for i, r in enumerate(remaining):
            if r[0] == tc_id:
                merged.append(r)
                del remaining[i]
                break
    merged.extend(remaining)
    return merged
```

and in `complete_round()`:

```python
    results = _merge_in_declared_order(
        tool_calls, [*state.collected.values(), *state.prep_failures]
    )
```

### Details

- No new imports; `list[dict]` / `list[tuple]` annotations match the existing `tool_calls:
  list[dict]` and `results` shapes.
- Budget per Plan: helper 25-35 lines including its docstring; `check_module_size.py` (20480 B gate,
  module is 2264 B) and `radon cc -n C` are hard gates inside this step (`AC-8`).
- `complete_round()`'s public docstring and `RoundState` stay byte-identical — the generated
  reference table (`tools/generate_reference_table.py`) only carries public top-level symbols
  (ADR-015 guard); `_merge_in_declared_order` (new) is private and must not appear in it.
- Mutation guard (`AC-7`): after the change, `grep -n 'tc\["id"\]' scripts/agent/tool_round_completion.py` must return no match (today `:47` matches).

## Compatibility considerations

- For valid unique-id batches the walk reproduces today's sorted output exactly (each entry matches
  its own result in order), so `REQ-005` anchors (`test_results_sorted_to_original_call_order`,
  `test_results_restored_to_original_order_despite_concurrent_grouping`,
  `test_tool_meta_is_keyed_by_call_id_not_tool_name`,
  `test_denied_tool_call_is_returned_as_tool_message`) pass unmodified.
- Blast-radius check per `rules/toolchain.md`: `complete_round` has one production caller
  (`tool_runner.py::finish()`); `rg -l '\bcomplete_round\b' tests/` currently returns no test file
  (only a comment at `test_tool_runner.py:1038`), so the radius is known-small before the change.
- `collect()` sees the same tuple objects in a new order only; stats and `out_failed_keys`
  accounting logic is untouched.

## Security considerations

N/A: pure list reordering over already-produced tuples; no I/O, no ids minted, no secrets.

## Rollback considerations

Single-commit revert: the three removed lines plus the helper are self-contained; no persistence or
schema change is involved.

## Validation plan

- `uv run pytest tests/agent/test_tool_round_completion.py tests/agent/test_tool_runner.py tests/agent/test_tool_preparation.py tests/agent/test_tool_result_pairing.py -q` — all existing 87
  tests plus `T-1`..`T-5` pass (tests come from rows 2-3; run them first, TDD order per Plan Phase 2).
- Mutation check `T-6`: in a scratch copy restore `tc["id"]` (or wrap the merge in
  `try/except KeyError`) → at least one new test fails; restore afterwards.
- `grep -n 'tc\["id"\]' scripts/agent/tool_round_completion.py` → no match (`AC-7`).
- `uv run python tools/check_module_size.py` → exit `0`; `uv run radon cc
  scripts/agent/tool_round_completion.py -s -n C` → no block at rank C or worse.
- `uv run ruff format scripts/`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run
  lint-imports`, `uv run vulture scripts/ --min-confidence 80` → no new finding, no unused code, no
  new import.
- `uv run python tools/generate_reference_table.py --check` → no drift.

## Completion criteria

- A raw entry with no `id` key no longer raises in `complete_round()` (probes CASE A/C/D/E behave as
  recorded in the Plan `Revalidation record`); `T-1`..`T-5` and the mutation check pass; the `grep`
  guard, size gate, radon gate, and reference-table check are clean; existing 87 tests pass
  unmodified.

## Out of Scope

- `scripts/agent/tool_runner.py` (its guarded `RoundState` scan at `:433` and the `collected` /
  `pc_by_id` dict-keyed writes that cause the `D-3` duplicate-id collapse stay as-is; `D-3` is
  documented, not engineered around — doc row 4).
- `scripts/agent/tool_preparation.py` (`REQ-006`: untouched), `scripts/agent/tool_result_pairing.py`,
  `scripts/agent/tool_scheduler.py:277` (prepared calls guarantee `id`).
- The test files themselves (procedure docs `20261024-234513_02` and `20261024-234513_03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write failing tests first (procedure docs `_02` and `_03`, Plan Phase 2 order) | Completed | 20261025-0100 | 20261025-0100 | TDD gate for this row |
| 2 | Add `_merge_in_declared_order()` (new) and replace `complete_round()` `:47-49` | Completed | 20261025-0100 | 20261025-0100 | every other statement unchanged |
| 3 | Run targeted tests, mutation check `T-6`, `grep` guard, size/radon gates | Completed | 20261025-0100 | 20261025-0100 | |
| 4 | Run the lint/types/security/architecture sequence + reference-table check | Completed | 20261025-0100 | 20261025-0100 | `rules/toolchain.md` |

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
- **Requirement ID**: `REQ-001` (lenient batch ordering), `REQ-002` (distinct batch positions),
  `REQ-003` (unmatched results appended last), `REQ-004` (empty `tool_call_id` preserved),
  `REQ-005` (valid-batch behavior unchanged), `REQ-009` (size/complexity gates)
- **Source issue**: `issues/20261021-093421_tool004-missing-tool-call-id-raises-keyerror.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-023815_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-234513
- **Related target files**: `scripts/agent/tool_round_completion.py`
