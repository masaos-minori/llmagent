## Goal

Correct the per-turn degraded-state bookkeeping inside `handle_memory_injection` in `scripts/agent/conversation_state_manager.py`. Today the method sets `ctx.conv.memory_disabled = True` on injection failure (lines 142-146) and never clears it, and it emits a `logger.warning` on every failing turn. This Plan confines the fix to that single method: clear the flag and re-arm the warning flag when a later injection attempt succeeds, and log the failure at warning level only on the False-to-True transition (steady-state degraded turns log at debug). No change to the call site, startup paths, or REPL display logic.

## Scope

- **In-Scope** (`scripts/agent/conversation_state_manager.py` only):
  - Capture the pre-injection degraded state before the `try` block.
  - Gate the failure-path log level on the False-to-True transition.
  - Add a `try/else` recovery branch that clears `memory_disabled`, resets `memory_warning_shown`, and logs one recovery warning when a previously-degraded session recovers.
- **Out-of-Scope** (owned by sibling rows / other artifacts):
  - `scripts/agent/context.py` field-comment update (row 02; REQ-004).
  - The regression module (row 03; REQ-001..REQ-003).
  - The memory overview doc (row 04; REQ-005).
  - The per-turn call site in `scripts/agent/workflow_engine_adapter.py` (reference only; MUST NOT be modified — the retry mechanism this Plan builds on lives there).
  - Startup failure path in `scripts/agent/startup_prompt_setup.py` (reference only; unchanged because the new clear-on-success rule recovers its flag).

## Assumptions

- `handle_memory_injection` is invoked once per turn from `workflow_engine_adapter.py` L321 with no `memory_disabled` gate, so injection already retries every turn; the defect is bookkeeping only (Path A in the Plan).
- The failure signal is an exception raised by `memory.on_user_prompt`; an empty snippet list is a successful call and counts as healthy (matches the current except-block semantics and the Plan's success-detection rule).
- `memory_disabled` has exactly five repository references (repl.py, conversation_state_manager.py, repl_input_loop.py, startup_prompt_setup.py, context.py); none gate execution, so changing its lifecycle cannot alter turn behavior.
- The module `logger` (defined at line 23) supports both `debug` and `warning` levels.

## Design decisions

- **Capture before the `try`.** Read `ctx.conv.memory_disabled` into a local `previously_degraded` (new) before entering `try`, so both the `except` and a new `else` can compare against the pre-attempt state.
- **`try/except/else` for recovery.** Use Python's `else` clause (runs only when `on_user_prompt` returned without raising) as the recovery branch, keeping the success path visually adjacent to the failure path and guaranteeing the recovery code never runs on an exception.
- **Transition-only logging.** Warning on the two transitions (False-to-True on failure, True-to-False on recovery); steady-state degraded turns log at debug. This bounds logging to one warning per degradation period without timers (retry cadence equals turn cadence).
- **Preserve user-facing gating.** Keep the existing `memory_warning_shown` set-on-failure logic untouched; the recovery branch resets it so a later degradation re-warns once.

## Alternatives considered

- **A dedicated degraded-state helper.** Rejected: the logic is four lines confined to one method; a helper would add a call-site change for no reuse.
- **Clearing the flag unconditionally at the end of the method.** Rejected: a still-degraded turn would then report healthy; the Plan requires clearing only on genuine success (no exception).

## Implementation

### Target file

`scripts/agent/conversation_state_manager.py` (existing; method body extended)

### Procedure

1. As the first statement inside the `if ctx.services_required.memory is not None:` guard (before the existing `try:` at line 125), capture the pre-attempt state: `previously_degraded = ctx.conv.memory_disabled`.
2. In the existing `except` block (lines 142-146), replace the unconditional `logger.warning("Memory injection failed: %s", e)` call with a transition-gated branch: `logger.debug(...)` when previously_degraded is truthy (steady-state degraded), `logger.warning(...)` when it is falsy (the False-to-True transition). Leave the `ctx.conv.memory_disabled = True` assignment and the `memory_warning_shown` gating below it unchanged.
3. After the `except` block, add a `try/else` `else:` clause that runs only when `on_user_prompt` returned without raising. Inside, when previously_degraded is truthy, set `ctx.conv.memory_disabled = False`, set `ctx.conv.memory_warning_shown = False`, and emit one recovery warning through the module `logger`. When previously_degraded is falsy, the `else` body is a no-op (healthy-to-healthy).
4. Confirm the success path still appends the memory block when snippets are present (lines 130-141 unchanged) and that an empty-snippet success (no append) still clears a degraded flag via the `else` branch (REQ-001).
5. Run the validation sequence (`routing.md`).

### Method

The current `handle_memory_injection` body (lines 121-146) opens a `try` at line 125 and handles failure in a single `except`. The edit adds a pre-`try` read, a transition-gated log in the `except`, and a new `else` recovery branch:

```
if ctx.services_required.memory is not None:
    previously_degraded = ctx.conv.memory_disabled      # NEW: capture before try
    try:
        memory_snippets = await ctx.services_required.memory.on_user_prompt(...)
        if memory_snippets:
            ... append memory block ...                  # lines 130-141 unchanged
    except Exception as e:
        if previously_degraded:                          # NEW: gated log level
            logger.debug("Memory injection failed: %s", e)
        else:
            logger.warning("Memory injection failed: %s", e)
        ctx.conv.memory_disabled = True                  # unchanged
        if not ctx.conv.memory_warning_shown:            # unchanged
            ctx.conv.memory_warning_shown = True
    else:                                                # NEW: ran only when no exception
        if previously_degraded:
            ctx.conv.memory_disabled = False             # NEW: clear degraded state
            ctx.conv.memory_warning_shown = False        # NEW: re-arm warning flag
            logger.warning("Memory injection recovered; degraded state cleared")
```

### Details

- **`REQ-001` / `AC-001` (clear on success):** the new `else` branch runs whenever `on_user_prompt` returns without raising, including when it returns an empty list (no append), so `memory_disabled` is cleared on any successful attempt.
- **`REQ-002` / `AC-002` (re-arm warning flag):** the `else` branch resets `memory_warning_shown` to `False` on recovery, so a subsequent degradation period re-warns once.
- **`REQ-003` / `AC-003` (transition-only logging):** the `except` logs at `warning` only on the False-to-True transition (when previously_degraded is falsy); persistent failures keep previously_degraded true and log at `debug`. No exception propagates out of the method.

## Compatibility considerations

- Purely additive control flow within one method: one new local, one conditional in the existing `except`, and one new `else` clause. No signature, call site, or other method changes; existing tests observe the same public behavior plus corrected flag values.

## Security considerations

- No new input surface or secret handling; the change is flag bookkeeping and log-level selection.

## Rollback considerations

- Revert the file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/conversation_state_manager.py` | Unit with fake memory service (fail/succeed sequences) | `uv run pytest tests/agent/test_memory_injection_recovery.py` | AC-001..AC-003 pass; one warning per degradation period |
| Existing behavior | Regression | `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py tests/agent/test_startup_prompt_setup.py` | Pass unchanged |
| Static | mypy / ruff | `uv run mypy scripts/`, `uv run ruff check scripts/` | Clean |

## Completion criteria

- `handle_memory_injection` captures the pre-attempt degraded state, logs the failure at warning only on the False-to-True transition (debug otherwise), and clears `memory_disabled` + resets `memory_warning_shown` on a successful attempt.
- `mypy` / `ruff` pass; the AC-005 regression suites pass unchanged.

## Out of Scope

- `scripts/agent/context.py` (row 02).
- The regression module (row 03).
- The memory overview doc (row 04).
- The call site in `workflow_engine_adapter.py` and the startup path in `startup_prompt_setup.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Clear-on-success + re-arm `memory_warning_shown` + transition-only logging in `handle_memory_injection` | Pending | — | — | REQ-001..REQ-003 |
| 2 | Add regression tests (row 03) | Pending | — | — | Dependency |
| 3 | Run validation sequence | Pending | — | — | pytest/mypy/ruff |
| 4 | Update field comments (row 02) + doc (row 04) | Pending | — | — | REQ-004, REQ-005 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261026-224838_memory001_retry-memory-injection-failure.md`
- **Source plan**: `plans/20261027-072306_memory001_retry-memory-injection-failure.md`
- **Generated at**: 20261027-112613
- **Related target files**: `scripts/agent/conversation_state_manager.py`
