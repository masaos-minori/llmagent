# Implementation: Add require_approval=True scenario test to test_orchestrator.py

Steps covered: Plan 20260626-090724 — Phase 3, Step 3-1

---

## Goal

Add a regression test to `tests/test_orchestrator.py` that verifies the `require_approval=True` + tool approval coexistence scenario, and that `workflow_require_approval` config is correctly threaded from `AgentConfig` into `WorkflowEngine`.

---

## Scope

- **In scope**: `tests/test_orchestrator.py` — add 1-2 new test functions
- **Out of scope**: changes to production code

---

## Assumptions

- `tests/test_orchestrator.py` already exists and has fixtures for `AgentContext`, `AgentConfig`.
- After step 2-1 (orchestrator.py change), `WorkflowEngine` receives `require_approval` from `ctx.cfg.workflow_require_approval`.
- The test should use a mock `WorkflowEngine` to verify the argument is passed correctly.

---

## Implementation

### Target file
`tests/test_orchestrator.py`

### Procedure
1. Read `tests/test_orchestrator.py` fully to understand existing fixture patterns.
2. Add a test function `test_workflow_engine_receives_require_approval_from_config`:
   - Build a minimal `AgentConfig` with `workflow_require_approval=True`.
   - Mock `WorkflowEngine` to capture the `require_approval` argument.
   - Call the orchestrator's workflow execution path.
   - Assert `WorkflowEngine` was called with `require_approval=True`.
3. Add a test function `test_workflow_engine_require_approval_false_by_default`:
   - Confirm that with default config (`workflow_require_approval=False`), `WorkflowEngine` receives `require_approval=False`.

### Method
Use `unittest.mock.patch` or `pytest-mock` `mocker.patch` to intercept `WorkflowEngine.__init__`.

### Details

Test skeleton:
```python
def test_workflow_engine_receives_require_approval_from_config(mocker):
    cfg = build_agent_config(workflow_require_approval=True)
    ctx = build_agent_context(cfg=cfg)
    mock_engine_cls = mocker.patch("agent.orchestrator.WorkflowEngine")
    
    # trigger workflow execution path in orchestrator
    ...
    
    init_kwargs = mock_engine_cls.call_args.kwargs
    assert init_kwargs["require_approval"] is True
```

Edge cases:
- `workflow_require_approval=True` with no active workflow: confirm no error (gate is only hit during workflow execution).
- `workflow_require_approval=False` (default): `WorkflowEngine` called with `require_approval=False`.

---

## Validation plan

- Run: `uv run pytest tests/test_orchestrator.py -x -v` — new tests must pass.
- Run: `uv run pytest tests/test_orchestrator.py -x` — no regressions.
- Type check: `mypy tests/test_orchestrator.py` — no new errors.
