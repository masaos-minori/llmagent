# tests/integration/test_orchestrator_integration.py: 17 tests fail with TypeError on MagicMock retry policy

## Priority
High

## Summary
17 tests in `tests/integration/test_orchestrator_integration.py` fail with
`TypeError: '>=' not supported between instances of 'int' and 'MagicMock'`
(or the equivalent `<=` variant). Root cause confirmed: the file's
`_patch_workflow_loader` fixture patches `agent.workflow_engine_adapter.WorkflowEngine`,
but `WorkflowEngineAdapter` now receives its `WorkflowEngine` instance via
constructor injection rather than constructing one internally at call time,
so the patch no longer intercepts anything and the real `WorkflowEngine`
runs against an unconfigured `MagicMock` workflow definition.

## Background
`scripts/agent/workflow_engine_adapter.py`'s `WorkflowEngineAdapter.__init__`
takes `workflow_engine: WorkflowEngine` as a required constructor parameter
(the error message at line 168, "WorkflowEngine must be injected via
constructor", documents this explicitly) and `execute_turn()` uses
`self._workflow_engine` directly (`engine = self._workflow_engine`) rather
than constructing a `WorkflowEngine(...)` instance itself. This looks like a
deliberate dependency-injection refactor of the adapter.

## Problem
`tests/integration/test_orchestrator_integration.py`'s `_patch_workflow_loader`
fixture (autouse) does:
```
with (
    patch("agent.orchestrator.WorkflowLoader"),
    patch("agent.orchestrator.StateStore"),
    patch("agent.workflow_engine_adapter.create_task", return_value=mock_task),
    patch("agent.workflow_engine_adapter.audit_workflow_start"),
    patch(
        "agent.workflow_engine_adapter.WorkflowEngine",
        return_value=mock_engine_instance,
    ),
):
    yield
```
The last patch targets the `WorkflowEngine` symbol as referenced from
`agent.workflow_engine_adapter` — this made sense when the adapter
constructed `WorkflowEngine(...)` itself at that call site. Now that the
engine is injected via the constructor (presumably built once during
`Orchestrator.__init__`, elsewhere), this patch has no effect on the actual
instance that ends up in `self._workflow_engine`: the *real*
`scripts/agent/workflow/workflow_engine.py::WorkflowEngine._run_stage_with_retry`
runs, using a `_wdef` (workflow definition) apparently sourced through the
also-patched-but-unconfigured `agent.orchestrator.WorkflowLoader` (patched as
a bare `MagicMock()` with no `return_value` set). That leaves
`_wdef.retry_policy.max_attempts` (and the stage's `timeout`) as
auto-generated `MagicMock` attributes instead of real numbers, so the retry
logic's numeric comparisons raise `TypeError` as soon as any exception
triggers the retry path — which happens for a large fraction of this file's
scenarios since `plan_fn`/`execute_fn`/`verify_fn` frequently raise inside
tests exercising error paths.

Confirmed by direct traceback inspection
(`uv run pytest tests/integration/test_orchestrator_integration.py -v -p no:randomly`):
```
scripts/agent/workflow/workflow_engine.py:254: in _run_stage_with_retry
    if attempt >= policy.max_attempts:
E   TypeError: '>=' not supported between instances of 'int' and 'MagicMock'
```
and, for the underlying original exception in cases that reach a retry
timeout check first:
```
scripts/agent/workflow/workflow_engine.py:321: in _run_stage
    artifact_uri = await asyncio.wait_for(fn(), timeout=timeout)
/usr/lib/python3.13/asyncio/tasks.py:494: in wait_for
    if timeout is not None and timeout <= 0:
E   TypeError: '<=' not supported between instances of 'MagicMock' and 'int'
```
Full run: `17 failed, 22 passed` in this file alone (all 17 failures share
this exact TypeError pattern; the 22 passing tests apparently take a code
path that never reaches the retry/timeout comparison).

## Reason for Change
Uncovered via a full `uv run pytest tests/` run while syncing to
`origin/master` via the `git-commit-and-sync` skill. This test file covers
core turn-execution and approval-workflow integration for the agent
orchestrator — a stale mock patch target leaves a large, correctness-
critical part of the orchestrator's behavior effectively unverified by CI
(the tests fail before their actual assertions run, so they provide zero
signal either way).

## Implementation Intent
Update `_patch_workflow_loader` to match the current dependency-injection
shape: either
(a) patch/inject a properly-configured fake `WorkflowEngine` instance at
whatever construction site now actually builds the real one and hands it to
`WorkflowEngineAdapter` (likely in `agent/orchestrator.py`'s
`Orchestrator.__init__` or wherever `WorkflowEngineAdapter(workflow_engine=...)`
is called), so `mock_engine_instance` (with its scripted `_engine_run` side
effect) is the instance actually used at `execute_turn()` time, or
(b) if a real `WorkflowEngine` must run for these tests, configure
`agent.orchestrator.WorkflowLoader`'s mocked return value to produce a
workflow definition with concrete (non-Mock) `retry_policy.max_attempts` and
stage `timeout` values instead of leaving it a bare, unconfigured
`MagicMock()`.
Prefer (a) — it matches this file's evident intent (tests read as unit-style
orchestrator tests that shouldn't need real workflow-engine retry semantics)
and requires touching only the test fixture, not inventing realistic retry
policy values that aren't otherwise meaningful to these tests.

## Target Files or Areas
- `tests/integration/test_orchestrator_integration.py` (`_patch_workflow_loader` fixture)
- `scripts/agent/workflow_engine_adapter.py` (`WorkflowEngineAdapter.__init__`, `execute_turn` — read to confirm exact injection point)
- `scripts/agent/orchestrator.py` (`Orchestrator.__init__` — read to find where `WorkflowEngine`/`WorkflowEngineAdapter` are actually constructed and wired together)

## Required Changes
- Identify the exact call site that now constructs the real `WorkflowEngine`
  and passes it into `WorkflowEngineAdapter`'s constructor.
- Update `_patch_workflow_loader` to patch `WorkflowEngine` at that call
  site (or otherwise ensure `mock_engine_instance` is what ends up injected),
  so the existing scripted `_engine_run` side effect actually runs instead of
  the real retry/timeout logic.
- Re-run the full file and confirm all 17 previously-failing tests pass with
  their actual assertions (not just "no longer raise TypeError").

## Constraints
Do not change `scripts/agent/workflow/workflow_engine.py`'s retry/timeout
comparison logic (`attempt >= policy.max_attempts`, `timeout <= 0`) — these
are correct given real, correctly-typed inputs; the bug is in test wiring,
not production code.

## Acceptance Criteria
- [ ] `uv run pytest tests/integration/test_orchestrator_integration.py -v` — 0 failures
- [ ] None of the 17 previously-failing tests merely stop raising `TypeError`
  without their actual behavioral assertions being exercised — confirm each
  test's `mock_engine_instance.run`/`_engine_run` path is genuinely invoked
- [ ] No other integration test regresses (`uv run pytest tests/integration/ -q`)

## Testing Expectations
`uv run pytest tests/integration/test_orchestrator_integration.py -v`
(targeted), plus `uv run pytest tests/integration/ -q` and
`uv run pytest tests/agent/ -q` for a regression check across orchestrator-
adjacent suites.

## Documentation Impact
N/A: test-fixture-only fix; the `WorkflowEngineAdapter` constructor-injection
design itself is out of scope (it is presumably already documented wherever
that refactor landed — verify against `docs/05_agent/*.md` only if the
investigation in Required Changes reveals the DI contract itself is
undocumented, which is a separate concern from this issue).

## Out of Scope
- Do not change `WorkflowEngineAdapter`'s constructor-injection design.
- Do not change `WorkflowEngine`'s retry/timeout logic.
- Do not investigate or fix any other file's test failures (filed
  separately: eventbus issues, `tests/agent/test_rag_get_cfg.py`).

## Dependencies
N/A: none

## Unresolved Questions
- Exact construction site: is `WorkflowEngine(...)` built once in
  `Orchestrator.__init__` and passed to `WorkflowEngineAdapter`, or is there
  an intermediate factory? Needs to be read directly from
  `scripts/agent/orchestrator.py` before writing the fixture fix.

## AI Implementation Instruction
Read `scripts/agent/orchestrator.py`'s `Orchestrator.__init__` and
`scripts/agent/workflow_engine_adapter.py`'s `WorkflowEngineAdapter.__init__`
in full before changing the test fixture, to find the exact symbol/call site
to patch. Change only `_patch_workflow_loader` in the test file — do not
touch production code. After the fix, verify each test's assertions are
actually being exercised (i.e. `mock_engine_instance.run` was called and its
`_engine_run` side effect ran plan_fn/execute_fn/verify_fn), not just that
the `TypeError` disappeared.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260917-110800
- **Related target files**: tests/integration/test_orchestrator_integration.py, scripts/agent/workflow_engine_adapter.py, scripts/agent/orchestrator.py
