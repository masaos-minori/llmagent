## Goal

Fix 3 `tests/agent/test_orchestrator.py` tests that share one confirmed root cause: `Orchestrator.__init__` eagerly constructs a real `WorkflowEngine(...)` and binds it as a fixed reference in `WorkflowEngineAdapter`, so a `WorkflowEngine` mock patched *after* `Orchestrator`/`_make_orchestrator` construction has no effect (REQ-001, REQ-002); and resolve whether the third test's expectation is still valid given `execute_turn`'s confirmed, deliberate `WorkflowHaltError`-swallowing design (REQ-003).

## Scope

In scope: `test_handle_turn_calls_workflow_engine_run_once`, `test_handle_turn_returns_normally_on_genuine_workflow_timeout`, `test_original_config_restored_even_on_error` in this file. Out of scope: `scripts/agent/orchestrator.py`'s eager `WorkflowEngine` construction and `scripts/agent/workflow_engine_adapter.py`'s fixed-reference storage/halt-swallowing — modify only if REQ-003's investigation confirms a genuine production gap, per this Plan's Implementation Target Files amendment requirement. `agent001`'s `ToolLoopGuard.check_all()` signature failures in this same file (distinct, already-tracked root cause).

## Assumptions

- Moving the `WorkflowEngine` patch to wrap `Orchestrator`/`_make_orchestrator` construction does not require restructuring any other test in the file that already correctly orders its patches — to be confirmed by the full-file rerun (Validation plan).

## Design decisions

- REQ-001/REQ-002: move `_make_orchestrator(ctx)`/`_make_orchestrator(ctx, on_error=on_error)` inside the `with patch("agent.workflow_engine_adapter.WorkflowEngine", return_value=mock_engine_instance):` block, so the mock is in effect when `Orchestrator.__init__` runs.
- REQ-003: investigate before fixing (per the Plan's Unknown UNK-01) — do not assume either the test or `execute_turn`'s halt-swallowing is wrong without tracing whether `handle_memory_injection`'s error path is meant to go through the engine's retry/halt machinery at all.

## Alternatives considered

- REQ-001/REQ-002: patching `orch._workflow_adapter._workflow_engine` directly after construction (the pattern already used correctly in `int001`'s `tests/integration/test_orchestrator_integration.py::test_handle_turn_invokes_workflow_engine_run`) instead of moving the `WorkflowEngine`-class patch earlier: considered equally valid — this document uses the class-patch-reordering approach since it requires a smaller diff (moving 1 line) than restructuring the `with` block to a direct attribute assignment; either is acceptable per the Plan's own Design section.

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. **REQ-001** (`test_handle_turn_calls_workflow_engine_run_once`): re-confirm the current structure via Read — `ctx = _make_ctx(); orch = _make_orchestrator(ctx)` occurs before the `with (patch("agent.workflow_engine_adapter.WorkflowEngine", ...), patch.object(orch._llm_executor, ...)):` block. Move `orch = _make_orchestrator(ctx)` to occur *inside* that `with` block, after the `WorkflowEngine` patch is active (the `patch.object(orch._llm_executor, ...)` line, which currently also depends on `orch` already existing, must be reordered to come after `orch`'s now-later construction, or restructured into a nested `with` — confirm the cleanest restructuring via Read of the exact current code before editing).
2. **REQ-002** (`test_handle_turn_returns_normally_on_genuine_workflow_timeout`): apply the same reordering — move `orch = _make_orchestrator(ctx, on_error=on_error)` inside the `with (...)` block that patches `agent.workflow_engine_adapter.WorkflowEngine`.
3. **REQ-003** (`test_original_config_restored_even_on_error`): trace whether `handle_memory_injection`'s error path (patched via `patch.object(orch._conversation_manager, "handle_memory_injection", side_effect=_raise)`) is invoked from within the engine's `execute_fn`/stage machinery (and thus subject to retry/halt-swallowing) or from an earlier, non-engine-mediated code path in `handle_turn`. Add temporary tracing/logging if needed to confirm the exact call chain. If it's confirmed to be *within* the engine's stage machinery: this test's `pytest.raises(RuntimeError)` expectation is likely incompatible with the confirmed halt-swallowing design — re-express the test's assertion to match the halt-swallowing outcome (e.g. assert `_handle_workflow_halt` was invoked and `ctx.cfg.tool.allowed_tools` was still restored to `[]`, without expecting an exception to reach the test). If it's confirmed to be *outside* the engine's stage machinery (i.e. `handle_memory_injection` normally runs before/independent of `WorkflowEngine.run()`): this is a genuine production gap (the error is unexpectedly being routed through the engine) — stop and report `Blocked: additional target file discovered — scripts/agent/workflow_engine_adapter.py` (or wherever the actual routing occurs) pending Plan amendment, rather than silently fixing only the test.

### Method

Steps 1-2: mechanical `with`-block restructuring (construction-order fix). Step 3: investigative tracing first, then a conditional test-assertion rewrite or a stop-and-report — not a blind edit.

### Details

- REQ-001/REQ-002: the exact restructuring must preserve `patch.object(orch._llm_executor, "handle_llm_turn", ...)`'s dependency on `orch` already existing — likely resulting in: `with patch("agent.workflow_engine_adapter.WorkflowEngine", return_value=mock_engine_instance): orch = _make_orchestrator(ctx); with patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(...)): await orch.handle_turn("hello")` (nested `with`), or an equivalent flattened form — confirm via Read which reads more naturally given this file's existing style before finalizing.
- REQ-003: this test's own docstring is "ctx.cfg.tool.allowed_tools is restored even when an exception propagates" — the core intent (config restoration) may remain valid even if the *mechanism* of "exception propagates" needs to change to "halt is handled internally, but restoration still occurs" per the confirmed halt-swallowing design; preserve the config-restoration assertion (`assert ctx.cfg.tool.allowed_tools == []`) regardless of how the exception-expectation part resolves.

## Compatibility considerations

- REQ-001/REQ-002: no production change; test-only fix. REQ-003: if it resolves to a production fix (pending Plan amendment), compatibility impact TBD.

## Security considerations

N/A: none of these 3 fixes touch security-relevant behavior.

## Rollback considerations

- REQ-001/REQ-002: `git revert` the commit, or manually restore the prior construction order. REQ-003: TBD pending investigation outcome.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_orchestrator.py` | Unit | `uv run pytest tests/agent/test_orchestrator.py -q` | All tests pass except `agent001`'s separately-tracked failures |
| Concurrency/timing sanity (if REQ-003 modifies production code) | N/A | N/A | Confirm via re-running the full file that no other test depends on the current halt-swallowing behavior in a way this change would break |

## Completion criteria

- REQ-001: `test_handle_turn_calls_workflow_engine_run_once` passes, with `mock_engine_instance.run` genuinely called once.
- REQ-002: `test_handle_turn_returns_normally_on_genuine_workflow_timeout` passes, with `on_error` genuinely invoked with the timeout error.
- REQ-003: either the test passes with a confirmed-correct re-expressed assertion, or this row is reported `Blocked: additional target file discovered` pending Plan amendment.
- `uv run pytest tests/agent/test_orchestrator.py -q` (full file) passes with no other regression.

## Out of scope

- `agent001`'s `ToolLoopGuard.check_all()` signature failures in this same file (distinct, already-tracked root cause).
- `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py` (confirmed correct unless REQ-003 says otherwise).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-164316 | 20260927-164316 |  |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing/investigating the existing 3 tests is itself the work |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A unless REQ-003 resolves to a documented contract change |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003: fix mock-ordering and resolve the third test's halt-swallowing question
- **Source issue**: issues/20260927-075259_agent008_orchestrator-workflow-engine-run-not-invoked-in-handle_turn-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085620_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093404
- **Related target files**: tests/agent/test_orchestrator.py