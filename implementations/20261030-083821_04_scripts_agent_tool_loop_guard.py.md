# Implementation Procedure: tool_loop_guard.py unavailable-repeat bound

## Goal

Teach `scripts/agent/tool_loop_guard.py` a bounded per-server unavailable-repeat counter
with an observable system hint and recovery clearing (REQ-003, REQ-004; plan AC-2, AC-3).

## Scope

**In scope:**
- `scripts/agent/tool_loop_guard.py`: hint constant, `observe_availability()`,
  `scan_unavailable_repeat()`, `check_unavailable_repeat()`, per-instance counter dict.
- Disclosed supporting edit (plan UNK-03, Needs confirmation): one call-site line in
  `scripts/agent/tool_runner.py::_run_prepared_call` — `guard.observe_availability(result)`
  next to the existing `_record_transport_failure(ctx, name, result)` /
  `guard.record_tool_result(name, text)` block (`tool_runner.py:227-229`). It is the only
  site that sees the `ToolCallResult`; without it the guard cannot observe hints.

**Out of scope:**
- New config keys: the bound reuses `cfg.tool.tool_empty_result_max_repeats`
  (plan Assumption UNK-2 resolution). Default `0` (`config_dataclasses.py:178`) keeps the
  new guard OFF until configured.
- `TurnLoopState` fields unchanged; empty-result guard behavior unchanged.

## Assumptions
- Verified at HEAD `124e340b4`: `ToolLoopGuard` (`tool_loop_guard.py:85`) is constructed
  per LLM turn (`llm_turn_executor.py:83`); `_save_guard_hint` persists
  `guard_hint` diagnostics (`:130`); `record_tool_result`/`scan_empty_result_repeat`/
  `check_empty_result_repeat` (`:158-200`) are the pattern to mirror;
  `ctx.cfg.tool.tool_empty_result_max_repeats` resolves the bound.
- Hinted results arrive only via the disclosed `tool_runner.py` call site.

## Design decisions
- `UNAVAILABLE_REPEAT_HINT` (new) module constant in the style of `EMPTY_RESULT_REPEAT_HINT`:
  "[System] The same MCP server was unavailable repeatedly. Stop selecting its tools in
  this turn and provide your best answer with the information already available."
- `observe_availability(result: ToolCallResult) -> None`: when `result.availability_hint`
  is not None, increment `self._unavailable_counts[result.server_key]`; when it is None
  (success or unhinted error), reset that key to 0 — this single reset rule is both
  recovery clearing (REQ-004/AC-3, including HALF_OPEN trial success) and the
  false-positive protection named in the plan Risks.
- Counter lives on the guard instance (`_unavailable_counts` (new), beside
  `_empty_result_counts` in `__init__`), so it is per-turn by construction; key is
  `server_key`, never tool name (unavailability is server-scoped).
- `check_unavailable_repeat()` mirrors `check_empty_result_repeat`: limit ≤ 0 → disabled;
  at `count >= limit` → one `logger.warning`, one `_save_guard_hint(guard_type=
  "unavailable_repeat", server_key=..., repeat_count=..., hint=UNAVAILABLE_REPEAT_HINT)`,
  return `"Repeated unavailability from server '<key>' detected."` Runner-side turn
  termination (row 05) provides the bound effect, mirroring how empty-result repeats
  end the turn.
- `report_effective_state()` output string is left byte-identical (existing tests assert
  its shape); surfacing the unavailable dial is deferred to UNK-02 follow-up.

## Alternatives considered
- Reusing `record_tool_result(name, text)` with an extended signature: rejected — that
  path is success-only and text-only; hints ride on error `ToolCallResult`s, so a
  distinct `observe_availability(result)` keeps both existing semantics untouched.
- A dedicated tool_unavailable_max_repeats config key: deferred per plan UNK-02; the
  reuse decision is recorded there.

## Implementation
### Target file
`scripts/agent/tool_loop_guard.py`

### Procedure
1. Add `UNAVAILABLE_REPEAT_HINT` (new) constant with the other hint constants.
2. Add `self._unavailable_counts: dict[str, int] = {}` in `__init__`.
3. Add `observe_availability()`, `scan_unavailable_repeat()`, `check_unavailable_repeat()`
  following the empty-result-repeat helpers' structure.
4. Disclosed supporting edit in `scripts/agent/tool_runner.py`: call
   `guard.observe_availability(result)` for every produced result (success and error).

### Method
- Additive methods; mirror existing guard idioms (`scan_*` pure, `check_*` emits).

### Details
- Import `ToolCallResult` from `shared.transport_dto` (agent→shared import is contract
  legal); do not import health gating from `shared.mcp_health` into the guard — the guard
  keys only on the result's hint (plan Design: guard never consults registry routing
  internals; `lint-imports` gate).

## Compatibility considerations
- With `tool_empty_result_max_repeats = 0` (repo default) the new bound is off: no
  observable behavior change for current deployments.
- Diagnostics consumers gain a new `guard_type` value only.

## Security considerations
- Hint text is a fixed constant; server-controlled strings never enter it (only
  `server_key`, already operator-owned).

## Rollback considerations
- Reverting the guard removes the methods; the disclosed `tool_runner.py` line would then
  raise AttributeError and must be reverted in the same change (single atomic commit
  recommended for rows 04/05 + wiring).

## Validation plan
- Row 10 (`tests/agent/test_tool_loop_guard.py`): counting to the configured bound fires
  exactly one `_save_guard_hint`; unhinted result resets; limit 0 disables;
  `RuntimeTool` static-field snapshot equality across health transitions (REQ-007).
- `uv run pytest tests/agent/test_tool_loop_guard.py
  tests/agent/test_tool_loop_guard_wiring.py` (wiring characterization stays green).

## Completion criteria
- Bound fires and hint observable at the configured limit; success resets counters;
  default-off behavior confirmed; static-visibility tests pass.

## Out of Scope
- Runner turn termination wiring (row 05), runner test harness (row 11), docs (row 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add hint constant, counter, `observe_availability` (new), `scan_*`, `check_*` | Pending | — | — | |
| 2 | Disclosed `tool_runner.py` call-site line (UNK-03, Needs confirmation) | Pending | — | — | |
| 3 | Run `uv run pytest tests/agent/test_tool_loop_guard*` green incl. existing wiring tests | Pending | — | — | |
| 4 | Run mypy and `lint-imports` | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `scripts/agent/tool_loop_guard.py`
