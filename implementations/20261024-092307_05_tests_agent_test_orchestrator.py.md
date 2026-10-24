## Goal

Add `TestTurnEndBracket` to `tests/agent/test_orchestrator.py` that witnesses the Orchestrator
bracket emits exactly one `turn_end` on every exit path and leaves clean turn/workflow state
(`REQ-002`, `REQ-004`). These tests are expected to FAIL against the current code (duplicate
`turn_end` on success, missing on failure) and PASS after the orchestrator sibling lands.

## Scope

- **In-Scope**: adding the `TestTurnEndBracket` class covering cases A, C, halt, escaped exception
  (G), cancellation (E), and a failure raised before `_activate_workflow`.
- **Out-of-Scope**: migrating any other call site (`_process_turn` call sites belong to turn002),
  editing the `_make_ctx` / `_make_orchestrator` harness (`:35-140`), or touching the guard test
  `test_original_config_restored_even_on_error` (`:1249-1273`).

## Assumptions

- The autouse `_patch_workflow_loader` fixture (`:142-…`) provides a mock engine that runs all
  three stages, making all five exit paths reachable without a real engine.
- `ctx.services_required.audit_logger` is `None` in `_make_ctx` (`:79`); the new tests install a
  capturing logger to observe emitted events.
- The adapter sibling has removed its own `turn_end` emit, so the count comes solely from the
  Orchestrator bracket.

## Design decisions

- Drive each exit path through the same `execute_turn` entry point rather than calling internal
  helpers, so the tests assert observable behavior (event count + fields + teardown) end-to-end.
- Capture `turn_end` events by installing a spy on `audit_logger.info` and parsing the JSON payload,
  mirroring how the production emitter serializes events.

## Alternatives considered

`N/A: asserting on private builder outputs would couple the test to the adapter (now deleted);
asserting on the emitted audit events is the stable contract (`REQ-002`).`

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. Add a capturing-audit-logger helper (or reuse an existing one) that records each dict passed to
   `audit_logger.info`, keyed by its `event` field.
2. In `_make_ctx` (or a per-test factory), set `ctx.services_required.audit_logger` to the
   capturing logger (it is `None` at `:79`).
3. Add class `TestTurnEndBracket` with these cases:
   - **A (success)**: one `turn_end`; `task_id` set, `workflow_id` set, `elapsed_ms` is
     turn-relative (small, not ~56 million), `error_kind` is `None`; workflow state deactivated.
   - **C (soft LLM error, partial)**: one `turn_end`; `error_kind='PREMATURE_EOF'`,
     `partial_completion=True`; soft-error fields preserved.
   - **halt** (`WorkflowHaltError`): one `turn_end`; teardown ran; `self._on_error` invoked.
   - **G (escaping non-retryable exception)**: one `turn_end`; `error_kind='RuntimeError'` (the
     exception class name); turn id cleared; exception re-raised.
   - **E (`asyncio.CancelledError` at stage boundary)**: one `turn_end`; `error_kind='CancelledError'`;
     turn id cleared (not left set).
   - **failure before `_activate_workflow`**: one `turn_end`; teardown ran.
4. Each case asserts: exactly one `turn_end` captured, the fields above, and that
   `deactivate_workflow` was called (workflow active is `False`).
5. Do not modify the guard test `test_original_config_restored_even_on_error` (`:1249-1273`) or
   the harness patches at `:219-220`, `:248-249`, `:341-345`, `:440-444`, `:1950-1951`.

### Method

Add one test class; use the existing mock-engine fixture. Keep assertions on the public audit
event, not internal state.

### Details

- Against the CURRENT code these fail: case A sees two `turn_end` events (Orchestrator + adapter),
  cases E/G see zero, `elapsed_ms` is process uptime. They pass once the Orchestrator bracket and
  the adapter deletion both land.
- `elapsed_ms` is measured from `turn_started_at` captured before `emit_turn_start()`; the test
  asserts it is small (< a few thousand ms), ruling out the uptime bug (`REQ-001`).

## Compatibility considerations

The harness (`:35-140`) and its fixture are used as-is except for installing the capturing logger;
no existing test is altered, so the full suite stays green apart from the new class.

## Security considerations

`N/A: test-only change; no auth, secret, or input-handling change.`

## Rollback considerations

`N/A: revert the single commit.`

## Validation plan

- Run `TestTurnEndBracket` alone first against current code: expect failures on event counts for A
  (extra) and E/G (missing), on `elapsed_ms`, and on post-state for E/G — confirming the tests
  actually witness the bug.
- After the orchestrator + adapter siblings land, expect all `TestTurnEndBracket` cases to pass.
- Confirm `test_orchestrator.py:537-560`, `:564-590`, `:1249-1273` and the integration suite
  (`tests/integration/test_orchestrator_integration.py`, out of scope) still pass.

## Completion criteria

`TestTurnEndBracket` exists with cases A, C, halt, G, E, and pre-`_activate_workflow` failure, each
asserting exactly one turn-relative `turn_end` with the correct fields and completed teardown; the
class fails against current code and passes after the implementation siblings land.

## Out of Scope

The production changes in `orchestrator.py`, `workflow_engine_adapter.py`, `audit_event_emitter.py`,
`context.py`, and the doc passages are handled by sibling documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestTurnEndBracket` per Implementation > Procedure | Pending | — | — | witness for `AC-1`-`AC-4`, `AC-8`, `AC-9` |
| 2 | Add or update tests per Validation plan | Pending | — | — | expect failures on current code, pass after impl |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | full agent + integration suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: no doc edit in this file | | | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (one `turn_end` per exit path), `REQ-004` (teardown never
  skipped), `REQ-001` (turn-relative `elapsed_ms`)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `tests/agent/test_orchestrator.py`
