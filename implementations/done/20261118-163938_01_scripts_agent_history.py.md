## Goal

Rewrite `HistoryManager._apply_unit_drops` (`scripts/agent/history.py`) so dropping the
selected candidate units runs in a single linear pass over the history instead of
rebuilding the list once per dropped message (REQ-001), and add an equivalence test to
`tests/agent/test_history_manager.py` (REQ-002).

## Scope

**Release unit**: N/A: not part of a release unit

## Assumptions

- `count_chars` and `estimate_tokens` are additive over messages: `scripts/shared/token_estimation.py`
  sums per-message contributions by category, and `count_chars` in `history.py` sums
  per-message string lengths. Running totals (`total - sum(dropped-unit contributions)`)
  therefore reproduce `_is_over_any_limit(new_history)` exactly for every prefix of
  dropped units.
- Identity-based membership (`id(m)`) stays correct when two messages have equal content
  (they are distinct objects); the drop-id set keyed on `id()` preserves this.
- `_drop_candidate_units` / `_build_protected_ids` are unchanged, so the candidate units
  and protected tail produced for a given history are identical to the current run.

## Design decisions

- Preserve the existing decision loop exactly (importance-order consumption, the
  `_is_over_any_limit` + `len(new_history) - len(unit) >= 1` never-empty gate, early
  `break`) and replace only the per-message rebuild with a single O(N) filter keyed on a
  drop-id set accumulated under that gate. This yields byte- and identity-identical output
  while removing the O(k) per-message factor.
- Drive the over-limit gate with the real `count_chars` / `count_tokens` on whole
  histories and units (no reimplementation of the token estimator), so the gate cannot
  diverge from the current behavior.

## Alternatives considered

- Rebuild per unit with a per-unit id-set (`[x for x in new_history if id(x) not in unit_ids]`)
  removes the per-message factor but still does one O(N) scan per dropped unit → O(U·N);
  rejected because REQ-001 requires a single linear pass over the history.
- Precompute per-message contributions by reimplementing the `estimate_tokens` category
  logic → higher divergence risk; rejected in favor of calling the real functions on whole
  histories/units.

## Implementation

### Target file

`scripts/agent/history.py`

### Procedure

Replace the body of `_apply_unit_drops` (current lines 373-389) with a single-pass
partition that keeps the existing decision loop selecting which units to drop under the
over-limit + never-empty gate, and builds the result in one comprehension over `history`
keeping messages whose `id()` is outside the accumulated drop-id set. Do not touch
`_fallback_truncate`, `_drop_candidate_units`, `_build_protected_ids`, the selection
policy, or the gating/reporting in `compress()`.

### Method

Current body (lines 380-389):

```python
new_history = list(history)
for unit in drop_candidates:
    if (
        self._is_over_any_limit(new_history)
        and len(new_history) - len(unit) >= 1
    ):
        for m in unit:
            new_history = [x for x in new_history if x is not m]
    else:
        break
return new_history
```

The inner `for m in unit: new_history = [x for x in new_history if x is not m]` is
O(k·N) per dropped unit. Replace with:

```python
def _apply_unit_drops(
    self,
    history: list[LLMMessage],
    drop_candidates: list[list[LLMMessage]],
) -> list[LLMMessage]:
    """Drop whole candidate units while over limit, never emptying the history."""
    drop_ids: set[int] = set()
    remaining_chars = self.count_chars(history)
    remaining_tokens = self.count_tokens(history)
    remaining_len = len(history)
    for unit in drop_candidates:
        over_limit = (
            self._char_limit > 0 and remaining_chars > self._char_limit
        ) or (
            self._token_limit > 0 and remaining_tokens > self._token_limit
        )
        if over_limit and remaining_len - len(unit) >= 1:
            for m in unit:
                drop_ids.add(id(m))
            remaining_chars -= self.count_chars(unit)
            remaining_tokens -= self.count_tokens(unit)
            remaining_len -= len(unit)
        else:
            break
    if drop_ids:
        return [x for x in history if id(x) not in drop_ids]
    return list(history)
```

The inline over-limit check reproduces `_is_over_any_limit` exactly
(`_is_over_char_limit` = `self._char_limit > 0 and count_chars > self._char_limit`; the
token clause mirrors it). Because both counts are additive, the running totals equal
`count_chars` / `count_tokens` of the history at that iteration step, so the selected unit
prefix — and therefore the accumulated drop-id set — is identical to the nested scan's.
System messages are never in `drop_candidates`, so their contribution stays in the running
totals exactly as it stays in the current `new_history`.

### Details

- `self.count_tokens(x)` is called with the default `last_input_tokens=None`, so it returns
  `estimate_tokens(x)[0]`; calling it on the full history and on each unit keeps the totals
  consistent by additivity.
- The never-empty guard (running length minus the unit length `>= 1`) stops the loop before
  the history would be emptied, with no extra scan.
- When the accumulated drop-id set is empty (no unit dropped, or no candidates) the
  method returns `list(history)`.
  `list(history)`, matching the current no-op path.
- Equivalence proof rests on additivity: verify `scripts/shared/token_estimation.py`
  sums per message before trusting the running totals.

### Companion test files

- `tests/agent/test_history_manager.py`
  - Procedure: add an equivalence test that (1) defines a reference nested-scan copy of the
    current `_apply_unit_drops` inline, (2) builds several histories including a heavy
    truncation case where most units are dropped, (3) derives `drop_candidates` via
    `mgr._drop_candidate_units(history, mgr._build_protected_ids(history))`, and (4) asserts
    the rewritten `mgr._apply_unit_drops(history, drop_candidates)` produces the same
    message identities in the same order as the reference across every scenario.
  - Validation: run `uv run pytest tests/agent/test_history_manager.py`; the new
    equivalence test passes and the existing `_fallback_truncate` / `_apply_unit_drops`
    tests pass unchanged.

## Compatibility considerations

N/A: `_apply_unit_drops` is a private method called solely by `_fallback_truncate`; its
signature and returned list are unchanged.

## Security considerations

N/A: pure in-memory list partition; no new input handling or credential path.

## Rollback considerations

N/A: revert the commit (single function, identical-output refactor).

## Validation plan

| Target / Module | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/history.py` | Format + lint | `uv run ruff format --check scripts/agent/history.py` && `uv run ruff check scripts/agent/history.py` | Pass (no diff, no lint errors) |
| `scripts/agent/history.py` | Type check | `uv run mypy --no-namespace-packages scripts/agent/history.py` | No issues |
| `tests/agent/test_history_manager.py` | Equivalence + regression | `uv run pytest tests/agent/test_history_manager.py` | New equivalence test passes; existing fallback tests pass unchanged |

## Completion criteria

- `_apply_unit_drops` returns a list identical by identity and order to the reference
  nested-scan output for every tested scenario, including heavy truncation.
- The body performs a single comprehension over `history` for the removal (no
  per-message full-list scan); the decision loop and gate are preserved.
- `ruff format --check`, `ruff check`, `mypy --no-namespace-packages`, and the full
  `tests/agent/test_history_manager.py` suite all pass.

## Out of Scope

Selection policy, protected-turn handling, `_fallback_truncate` gating/reporting, token
estimation, and compression selection.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `_apply_unit_drops` to a single-pass partition (`scripts/agent/history.py`, REQ-001) | Completed | 20261118-1645 | 2026-11-18 | single-pass partition keyed on accumulated drop-id set; decision loop/gate preserved |
| 2 | Add equivalence test (`tests/agent/test_history_manager.py`, REQ-002) | Completed | 20261118-1645 | 2026-11-18 | equivalence test + heavy truncation minimal-floor test |
| 3 | Format/lint/type-check and run history tests | Completed | 20261118-1646 | 2026-11-18 | ruff format/lint clean, mypy no issues, 82/82 history tests pass |

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
- **Requirement ID**: REQ-001 (single-pass drop preserving identical output and invariants), REQ-002 (equivalence test covering heavy truncation)
- **Source issue**: issues/done/20261118-141240_histperf001_history-fallback-truncation-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142439_histperf001_history-fallback-truncation-cost.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-163938
- **Related target files**: `scripts/agent/history.py`, `tests/agent/test_history_manager.py`
