# Implementation Procedure: llm_turn_runner.py unavailable-repeat wiring

## Goal

Surface the unavailable-repeat bound in the turn loop of `scripts/agent/llm_turn_runner.py`
so a persistently unavailable server ends the turn through the guard bound instead of
unbounded re-selection (REQ-003; plan AC-2).

## Scope

**In scope:**
- `scripts/agent/llm_turn_runner.py`: one check after tool execution in the turn loop —
  `if msg := self._guard.check_unavailable_repeat(): return TurnResult(action="fail",
  answer=msg, reason="unavailable_repeat")`.

**Out of scope:**
- Hint feeding into the guard (that is the disclosed `tool_runner.py` call site owned by
  row 04, plan UNK-03).
- Turn-entry message injection (reserved to `toolexec001`; this row's wiring point is
  after `execute_all_tool_calls`, mirroring `check_empty_result_repeat`).

## Assumptions
- Verified at HEAD `124e340b4`: the runner already chains `check_empty_result_repeat`
  then `check_error_limit` immediately after `execute_all_tool_calls(...)`
  (`llm_turn_runner.py:116-133`); `TurnResult.action` is
  `Literal["continue", "fail"]` with a free-form `reason` (`turn_result.py:22-25`);
  `ToolLoopGuard` is constructed per turn in `llm_turn_executor.py:83`.
- `reason="unavailable_repeat"` is a new turn-end reason value; downstream consumers of
  `TurnResult.reason` treat unknown values as generic failures (existing reasons:
  `empty_result_repeat`, `error_limit`, `max_tool_turns`).

## Design decisions
- Check placement: directly after the `check_empty_result_repeat` branch and before
  `check_error_limit` — both repeat guards are evaluated before the error-limit guard,
  matching plan Design ("further identical calls ... refused the same way empty-result
  repeats are", i.e. end-of-turn fail, not mid-call interception).
- No new imports, no `TurnLoopState` changes: the counter lives on the guard instance.
- The system hint itself is persisted by the guard's `_save_guard_hint` (row 04); the
  runner only ends the turn with the summary answer, exactly like the empty-result path.

## Alternatives considered
- Interception inside `execute_all_tool_calls` per call: rejected — duplicates gating
  outside the guard's turn-scoped design and would change tool execution semantics the
  plan keeps frozen (advisory only, REQ-001).
- Surfacing the hint into the next prompt turn: deferred per plan Assumption (placement
  on the tool-error channel only; widening requires the AC-5 measurement).

## Implementation
### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure
1. Insert the `check_unavailable_repeat` (new) branch after the `check_empty_result_repeat`
  branch in the tool-call block.
2. No other line changes.

### Method
- Four-line insertion mirroring the neighboring guard branch.

### Details
- The disclosed `tool_runner.py` edit (row 04 step 2) is a prerequisite: without it the
  counter never increments and the branch is dead code (default-off is still safe).

## Compatibility considerations
- `toolexec001` risk (plan Risks): its pending-call control-message injection lands at
  turn entry; this check lands after tool execution. Whichever plan lands first, rebase
  this insertion point against current HEAD before applying.
- With `tool_empty_result_max_repeats = 0` (repo default) `check_unavailable_repeat()`
  returns None: behavior identical to today.

## Security considerations
- Runner surfaces only the guard's fixed summary string; no server-controlled text is
  added to turn answers beyond what the tool result already carried.

## Rollback considerations
- Removing the four-line branch fully reverts runner behavior; guard methods (row 04)
  become unused but harmless.

## Validation plan
- Row 11 (`tests/agent/test_llm_turn_runner.py`): a turn whose tool call results are
  persistently hinted-unavailable ends with `action="fail"`,
  `reason="unavailable_repeat"` at the configured bound; unhinted turns unchanged; LLM
  tool definitions in the request are unchanged between turns (REQ-002/AC-1).
- `uv run pytest tests/agent/test_llm_turn_runner.py`; mypy; `lint-imports`.

## Completion criteria
- Bounded end-to-end loop verified by row 11 integration test; default-off behavior
  unchanged; no new imports.

## Out of Scope
- Guard internals (row 04), hint production (rows 01-03), diagnostics display (row 06),
  REQ-006 measurement harness (row 11), docs (rows 12-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert `check_unavailable_repeat` (new) branch after `check_empty_result_repeat` | Pending | — | — | |
| 2 | Confirm runner test suite green with default config (bound off) | Pending | — | — | |
| 3 | Run mypy and `lint-imports` | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `scripts/agent/llm_turn_runner.py`
