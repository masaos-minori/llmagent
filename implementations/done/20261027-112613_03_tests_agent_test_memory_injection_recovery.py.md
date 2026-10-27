## Goal

Add a new regression module `tests/agent/test_memory_injection_recovery.py` that pins the per-turn degraded-state flag transitions introduced by this Plan: a single injection failure sets `memory_disabled` (AC-001), a later successful attempt clears it and re-arms `memory_warning_shown` (AC-001, AC-002), and N persistent failures emit exactly one warning-level log (the rest at debug) without raising (AC-003). The module drives the real `handle_memory_injection` method through a fake memory service so the behavior is pinned end-to-end.

## Scope

- **In-Scope** (`tests/agent/test_memory_injection_recovery.py`, new file):
  - One test class with three async methods covering AC-001..AC-003.
  - A module-level helper that builds a `ConversationStateManager` around a mocked `ctx` with a fake async memory service.
- **Out-of-Scope**:
  - Any change to `scripts/agent/conversation_state_manager.py` (row 01).
  - The field-comment update (row 02) and the memory overview doc (row 04).
  - Modifying existing memory tests listed in AC-005.

## Assumptions

- The `agent` package is importable under the test runner (existing tests import `agent.context.ConversationState`), so `agent.conversation_state_manager` and `agent.context` import cleanly.
- `pytest-asyncio` is configured (existing `tests/agent/test_startup_prompt_setup.py` uses `@pytest.mark.asyncio` and `async def` tests).
- `ConversationStateManager.__init__` takes a positional `ctx` and keyword-only `tasks` and `on_discard` (both required) plus optional `diagnostic_store`, `tracer`, `on_first_turn`, `on_error`.
- The failure signal is an exception raised by the fake `on_user_prompt`; an empty list return is a successful (healthy) call.
- The module logger is `agent.conversation_state_manager.logger`; patching its `warning`/`debug` methods counts transition logs deterministically.

## Design decisions

- **Fake memory service via `MagicMock` + `AsyncMock`.** A `MagicMock` `ctx` supplies `ctx.services_required.memory`; its `on_user_prompt` is an `AsyncMock` whose `side_effect`/`return_value` is switched between calls to simulate fail/succeed/fail. `ctx.conv` is a real `ConversationState` so the two flags are live attributes.
- **Drive the real method.** Tests call the actual `handle_memory_injection` rather than stubbing it, so the assertion is on observable flag/log behavior, not on an internal helper.
- **Count logs by patching the module logger.** Patching `warning` and `debug` on the module logger gives exact call counts for the transition-only rule (AC-003) without depending on caplog propagation config.
- **One class, three methods.** Each acceptance criterion maps to one method; the shared helper keeps the setup DRY.

## Alternatives considered

- **A real memory-service subclass.** Rejected: the mock path exercises the exact fail/succeed/fail sequence deterministically and avoids DB/embedding fixtures.

## Implementation

### Target file

`tests/agent/test_memory_injection_recovery.py` (new)

### Procedure

1. Create `tests/agent/test_memory_injection_recovery.py`. Declare the imports in prose at the top of the file: the standard-library `unittest.mock` helpers `MagicMock` and `AsyncMock` plus `patch`; the `pytest` framework marker decorator; the `logging` module; and the `agent` package classes `ConversationState` and `ConversationStateManager`. Do NOT emit literal import statements here — describe them as above in the written file.
2. Add a module-level helper (new) that builds and returns a three-tuple: a `ConversationStateManager` instance, its `MagicMock` `ctx`, and the fake `mem` service. Inside, construct a `MagicMock`, assign a real `ConversationState` to `ctx.conv`, set `ctx.session.session_id`, build a `MagicMock` `mem` with `mem.on_user_prompt` set to an `AsyncMock` returning an empty list, assign `mem` to `ctx.services_required.memory`, and construct the manager with `tasks=set()` and `on_discard` set to a no-op lambda.
3. Add the test class `TestMemoryInjectionRecovery` (new).
4. Add `test_failure_then_success_clears_flag` (new): build the fixture, set `mem.on_user_prompt` to raise, call `handle_memory_injection`, and assert `ctx.conv.memory_disabled` is `True`; then clear the side effect, make it return an empty list, call again, and assert `memory_disabled` is `False` (AC-001 / REQ-001).
5. Add `test_recovery_rearms_warning_flag` (new): fail once (assert both flags `True`), then succeed with an empty result (assert both flags cleared to `False`), then fail again (assert `memory_warning_shown` is `True` again — re-armed) (AC-002 / REQ-002).
6. Add `test_persistent_failure_warns_once` (new): wrap three consecutive failing calls in a `patch.object` context on the module logger's `warning` and `debug` methods, assert `warning` was called exactly once and `debug` at least twice, and assert no exception propagated and `memory_disabled` stays `True` (AC-003 / REQ-003).
7. Run the validation sequence (`routing.md`).

### Method

The class mirrors the shape of `tests/agent/test_startup_prompt_setup.py`: a module helper builds a `MagicMock` `ctx` with a real `ConversationState`, and each test switches the fake service's behavior between calls. The new helper additionally wires an `AsyncMock` onto `mem.on_user_prompt` and constructs the manager with the required keyword-only `tasks` and `on_discard`.

Illustrative reference implementation (adapt; do not copy verbatim). Imports are the standard-library unittest.mock helpers (MagicMock, AsyncMock, patch), the pytest marker, the logging module, and the agent.context.ConversationState and agent.conversation_state_manager.ConversationStateManager classes (declared at the top of the file per Procedure step 1):

```
import logging

import pytest
# from-line imports are declared at the file top (see Procedure step 1):
# unittest.mock (MagicMock, AsyncMock, patch); logging;
# agent.context.ConversationState; agent.conversation_state_manager.ConversationStateManager


def _build():
    ctx = MagicMock()
    ctx.conv = ConversationState()
    ctx.session.session_id = "test-session"
    mem = MagicMock()
    mem.on_user_prompt = AsyncMock(return_value=[])
    ctx.services_required.memory = mem
    mgr = ConversationStateManager(
        ctx, tasks=set(), on_discard=lambda task: None
    )
    return mgr, ctx, mem


class TestMemoryInjectionRecovery:

    @pytest.mark.asyncio
    async def test_failure_then_success_clears_flag(self):
        mgr, ctx, mem = _build()
        mem.on_user_prompt.side_effect = RuntimeError("fail")
        await mgr.handle_memory_injection("hi")
        assert ctx.conv.memory_disabled is True
        mem.on_user_prompt.side_effect = None
        mem.on_user_prompt.return_value = []
        await mgr.handle_memory_injection("hi")
        assert ctx.conv.memory_disabled is False

    @pytest.mark.asyncio
    async def test_recovery_rearms_warning_flag(self):
        mgr, ctx, mem = _build()
        mem.on_user_prompt.side_effect = RuntimeError("fail")
        await mgr.handle_memory_injection("hi")
        assert ctx.conv.memory_disabled is True
        assert ctx.conv.memory_warning_shown is True
        mem.on_user_prompt.side_effect = None
        mem.on_user_prompt.return_value = []
        await mgr.handle_memory_injection("hi")
        assert ctx.conv.memory_disabled is False
        assert ctx.conv.memory_warning_shown is False
        mem.on_user_prompt.side_effect = RuntimeError("fail")
        await mgr.handle_memory_injection("hi")
        assert ctx.conv.memory_warning_shown is True

    @pytest.mark.asyncio
    async def test_persistent_failure_warns_once(self):
        import agent.conversation_state_manager as csm_module

        mgr, ctx, mem = _build()
        with patch.object(csm_module.logger, "warning") as warn, patch.object(
            csm_module.logger, "debug"
        ) as debug:
            mem.on_user_prompt.side_effect = RuntimeError("fail")
            await mgr.handle_memory_injection("hi")
            await mgr.handle_memory_injection("hi")
            await mgr.handle_memory_injection("hi")
            assert warn.call_count == 1
            assert debug.call_count >= 2
            assert ctx.conv.memory_disabled is True
```

The three async methods drive the real `handle_memory_injection` through the fake service; the third patches the module logger (`agent.conversation_state_manager.logger`) to count the warning/debug calls that prove transition-only logging.

### Details

- **`REQ-001` / `AC-001`:** `test_failure_then_success_clears_flag` (new) asserts `memory_disabled` flips True on failure and back to False on an empty success.
- **`REQ-002` / `AC-002`:** `test_recovery_rearms_warning_flag` (new) asserts `memory_warning_shown` resets to False on recovery and re-arms to True on the next degradation.
- **`REQ-003` / `AC-003`:** `test_persistent_failure_warns_once` (new) asserts exactly one warning across N failures, debug on the repeats, and no exception escaping the method.

## Compatibility considerations

- Purely additive test module; no existing test or source file is modified, so the AC-005 regression suites keep passing.

## Security considerations

- Test-only additions; the fake service raises in-process exceptions only. No new input surface or secret handling.

## Rollback considerations

- Delete the new file (`git checkout` cannot restore an untracked file; remove it). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_memory_injection_recovery.py` | New: fail/succeed/fail transitions + warning count | `uv run pytest tests/agent/test_memory_injection_recovery.py` | AC-001..AC-003 pass; warning count per period == 1 |
| Existing memory tests | Regression (unchanged) | `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py tests/agent/test_startup_prompt_setup.py` | Pass unchanged |
| Static | mypy / ruff | `uv run mypy scripts/`, `uv run ruff check scripts/` | Clean |

## Completion criteria

- The new module has three passing async tests covering AC-001..AC-003; the AC-005 regression suites pass unchanged; `mypy` / `ruff` pass.

## Out of Scope

- Flag bookkeeping (`scripts/agent/conversation_state_manager.py`, row 01).
- Field comments (row 02).
- The memory overview doc (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Flag bookkeeping (row 01) | Completed | — | 20261027-185628 | Dependency Implemented and validated in the memory001 batch (full suite 10235 passed, diff coverage 98%) |
| 2 | Add regression module | Completed | — | 20261027-185628 | This row Implemented and validated in the memory001 batch (full suite 10235 passed, diff coverage 98%) |
| 3 | Run validation sequence | Completed | — | 20261027-185628 | pytest/mypy/ruff Implemented and validated in the memory001 batch (full suite 10235 passed, diff coverage 98%) |
| 4 | Update doc (row 04) | Completed | — | 20261027-185628 | REQ-005 Implemented and validated in the memory001 batch (full suite 10235 passed, diff coverage 98%) |

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
- **Related target files**: `tests/agent/test_memory_injection_recovery.py`