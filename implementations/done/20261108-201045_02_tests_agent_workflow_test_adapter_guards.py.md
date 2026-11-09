# tests/agent/workflow/test_adapter_guards.py

> **Source Plan**: `plans/20261108-084014_wfaudit013_adapter-production-asserts.md`
> **Generated**: 20261108-201045
> **Target file**: `tests/agent/workflow/test_adapter_guards.py` (new)
> **Release unit**: wfaudit013-full
> **Phase**: 2 — Regression tests

## Goal
Create `tests/agent/workflow/test_adapter_guards.py` with two regression tests that pin
the typed production guards added by sibling document
`implementations/20261108-201045_01_scripts_agent_workflow_engine_adapter.py.md`: the
wiring guard raises `WorkflowEngineWiringError` (new) and the turn-boundary guard raises
`TurnBoundaryMissingError` (new) (`REQ-002`).

## Scope
**Release unit**: wfaudit013-full

- Covers Plan `plans/20261108-084014_wfaudit013_adapter-production-asserts.md` row 2 only:
  `tests/agent/workflow/test_adapter_guards.py` (new file).
- The production guard edits themselves are owned by sibling document
  `20261108-201045_01_scripts_agent_workflow_engine_adapter.py.md` (row 1).

## Assumptions
- Line numbers refer to HEAD `ad48bfa28`. This document lands after sibling `20261108-201045_01`
  (the tests import the new error classes from `agent.workflow_engine_adapter`); it is also
  sequenced after `155554_01` and `162804_01` per batch chronology, but this file contains no
  anchors into the adapter source, so those shifts do not affect it.
- The tests fail on HEAD (`AssertionError`/silent path instead of the typed errors) and pass
  only after `20261108-201045_01` lands; they are pending regression coverage, not a
  red-first TDD gate.
- `tests/agent/workflow/` already exists (`test_engine.py`, `test_events.py`, `test_types.py`),
  so no new package init files are required.
- Adapter construction kwargs mirror the adapter construction in `scripts/agent/orchestrator.py`
  (L137-148); the fixture is adjusted only if the constructor signature changes before landing.

## Design decisions
- Dedicated new test file instead of extending `tests/agent/test_orchestrator.py`: that file
  is the target of two other pending procedures (`implementations/20261108-162804_02_*`,
  `implementations/20261108-175155_08_*`), so a new file avoids write contention and groups
  adapter-guard tests with the `tests/agent/workflow/` package.
- The boundary test asserts `audit_stage_completed` is never awaited, locking the
  guard-before-audit ordering implied by replacing the assert in place.
- `tests/agent/` is outside the mypy primary scope, so the wiring test can pass
  `workflow_engine=None` against the non-Optional annotation without a type error.

## Alternatives considered
- Add the tests to `tests/agent/test_orchestrator.py` near the existing adapter tests:
  rejected — two pending procedures target that file; simultaneous edits create merge risk.
- Duplicate the `_make_ctx` harness helper locally: rejected — importing from
  `tests.agent.test_orchestrator` keeps fixture behavior consistent and surfaces harness
  drift immediately.
- Reuse the wfaudit006 `TypeError`-pinning tests as the guard coverage: rejected — those
  tests cover pre-`initialize()` attribute injection and pin the opposite failure mode.

## Implementation
### Target file
`tests/agent/workflow/test_adapter_guards.py` (new)

### Procedure
Create the file with two async guard tests built on the existing adapter test harness.

### Method
1. Create the file with this content:

```
"""Regression tests for workflow adapter production guards (wfaudit013).

Two tests (REQ-002), both fail on HEAD and pass after
20261108-201045_01 lands: one for each typed guard error.
"""

from unittest.mock import AsyncMock, patch

import pytest

from agent.chat_models import TurnResult
from agent.state_store import StateStore
from agent.workflow_engine_adapter import (
    TurnBoundaryMissingError,
    WorkflowEngineAdapter,
    WorkflowEngineWiringError,
)
from tests.agent.test_orchestrator import _make_ctx


@pytest.mark.asyncio
async def test_missing_engine_raises_wiring_error(tmp_path):
    store = StateStore(str(tmp_path / "guard_state.db"))
    orchestrator = AsyncMock()
    orchestrator._store = store

    adapter = WorkflowEngineAdapter(
        orchestrator=orchestrator,
        workflow_engine=None,
        model="claude-sonnet-4-5",
        system_prompt="sp",
    )
    with pytest.raises(WorkflowEngineWiringError):
        await adapter.initialize()


@pytest.mark.asyncio
async def test_missing_boundary_raises_protocol_error(tmp_path):
    store = StateStore(str(tmp_path / "guard_state.db"))
    engine = AsyncMock()
    engine.can_handle.return_value = True
    engine.initialize.return_value = None
    engine.run.return_value = TurnResult(
        action="continue", answer="hi", persist_as_assistant=True
    )

    orchestrator = AsyncMock()
    orchestrator._store = store

    adapter = WorkflowEngineAdapter(
        orchestrator=orchestrator,
        workflow_engine=engine,
        model="claude-sonnet-4-5",
        system_prompt="sp",
    )
    await adapter.initialize()

    ctx = _make_ctx(store=store, session_id="s-missing-boundary")
    ctx.turn.persistence_boundary = None

    audit = AsyncMock()
    with patch("agent.workflow_engine_adapter.audit_stage_completed", new=audit):
        with pytest.raises(TurnBoundaryMissingError):
            await adapter.handle_llm_turn(ctx, "hello")
    assert audit.await_count == 0
```

### Details
- The `TurnResult` construction with `persist_as_assistant=True` matches the pattern of the
  existing adapter continue/abort turn tests in `tests/agent/test_orchestrator.py`.
- `_make_ctx` (L109) is imported, not duplicated.
- The `engine.run` mock returns a continue-turn result so execution reaches the
  persist-as-assistant branch where the boundary guard lives (in `_run_execute_stage`,
  before `await boundary.save("assistant", answer)`).

## Compatibility considerations
- Test-only addition: no production imports or public APIs change.
- The wfaudit006 `TypeError`-pinning tests in `tests/agent/test_orchestrator.py` stay as-is
  (their removal is owned by `162804_02`, sequenced before this file lands).

## Security considerations
- No secrets, subprocess, or network use; bandit does not scan `tests/`, and no suppression
  is needed or added.

## Rollback considerations
- Delete the file to revert; no other work item depends on it. If sibling `20261108-201045_01`
  is reverted while this file remains, both tests fail against HEAD behavior — delete or skip
  them together.

## Validation plan
- Targeted run on HEAD must fail both tests (`AssertionError` / no exception); after sibling
  `20261108-201045_01` lands both must pass:
  `uv run pytest -q tests/agent/workflow/test_adapter_guards.py`
- `uv run pytest tests/agent/ -q` then full `uv run pytest tests/ -q` stay green.
- `uv run ruff check tests/agent/workflow/test_adapter_guards.py` and
  `uv run ruff format --check tests/agent/workflow/test_adapter_guards.py` clean.

## Completion criteria
- Both tests exist and pass with the typed guards landed; both fail when either guard is
  reverted; lint and format gates clean; no changes outside the new file.

## Out of Scope
- Production guard edits (owned by sibling document `20261108-201045_01`).
- Removing or reworking the wfaudit006 `TypeError`-pinning tests in
  `tests/agent/test_orchestrator.py` (owned by `162804_02`).
- The `assert` statements in `tests/agent/workflow/test_engine.py` (test-side asserts are
  outside the plan's `scripts/` scope).
- `docs/05_testing.md` updates: the plan's docs mapping has no docs row, so the docs scope
  check records verified no-change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create file per Implementation > Method | Done | 20261109-... | 20261109-... | Rewritten against the current `execute_turn`-based adapter API (see Blocker Log). |
| 2 | Run tests, validation, and checks per Validation plan | Done | 20261109-... | 20261109-... | Both tests pass; ruff format/check clean; `tests/agent/` 4248 passed / 3 skipped, no new failures. |

### Rewrite notes (deviation from the original procedure)
The original procedure was drafted against the pre-`wfaudit008` adapter API
(`adapter.initialize()`, `adapter.handle_llm_turn(ctx, ...)`, constructor
`orchestrator=/model=/system_prompt=`), which no longer exists. It was rewritten
against the current surface:

- Construction mirrors `tests/agent/workflow/test_adapter_alias_surface.py`:
  `WorkflowEngineAdapter(ctx, *, state_store, workflow_engine, conversation_manager,
  llm_executor)` with injected mocks — no real store/engine.
- Imports fixed: `TurnResult` from `agent.turn_result` (was the bogus
  `from agent.chat_models import TurnResult`); the bogus `from agent.state_store
  import StateStore` dropped (a `MagicMock` stands in for the store).
- Wiring guard driven via `await adapter.execute_turn(...)`; the boundary guard is
  reached by returning a `TurnResult(action="continue", persist_as_assistant=True)`
  from `llm_executor.handle_llm_turn` with `ctx.turn.persistence_boundary = None`.
  `_prepare_turn_input`'s async `conversation_manager` methods are stubbed as
  `AsyncMock`; `classify_and_inject_mode` is patched to a no-op so the turn reaches
  the execute stage.
- **Production change (scope expansion, self-adjudicated):** the wiring guard was
  moved to the top of `execute_turn`, before `_init_workflow_task` /
  `_activate_workflow`, which dereference `self._workflow_engine.version`. On the
  pre-fix code the guard was unreachable dead code — a `None` engine raised
  `AttributeError` instead of `WorkflowEngineWiringError`. The rewrite converts the
  bare `assert` to `if ... raise` (consistent with the boundary guard) and moves it up.
  Behavior-preserving in production (the engine is always injected); required for the
  regression test to assert the typed error rather than an `AttributeError`.

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Sibling test content drafted against the pre-`wfaudit008` adapter API (`initialize()`/`handle_llm_turn()`, wrong constructor, wrong imports) — `ModuleNotFoundError` on import. Procedure 01 targets the current API; procedure 04 targeted the old one. | Resolved by rewriting the tests against the current `execute_turn`-based API (option A, user-approved 2026-11-09). | 20261109 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (typed guard regression tests)
- **Source issue**: `issues/20261107-203226_wfaudit013_adapter-production-asserts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084014_wfaudit013_adapter-production-asserts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-201045
- **Related target files**: `tests/agent/workflow/test_adapter_guards.py`, `scripts/agent/workflow_engine_adapter.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-201045 -->
