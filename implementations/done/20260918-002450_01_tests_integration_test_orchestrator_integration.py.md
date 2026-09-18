Update `_patch_workflow_loader` fixture in `tests/integration/test_orchestrator_integration.py` to patch `WorkflowEngine` and `StateStore` at the correct call sites (`agent.orchestrator.*` and `agent.workflow_engine_adapter.*`) so the existing scripted `_engine_run` side effect actually runs instead of the real retry/timeout logic and database access.

## Scope
- **In-Scope**: Update `_patch_workflow_loader` fixture to patch `WorkflowEngine` and `StateStore` at the correct construction sites (`agent.orchestrator.WorkflowEngine`, `agent.orchestrator.StateStore`, `agent.workflow_engine_adapter.WorkflowEngine`, `agent.workflow_engine_adapter.StateStore`).
- **Out-of-Scope**: Do not change `scripts/agent/workflow/workflow_engine.py`'s retry/timeout comparison logic (`attempt >= policy.max_attempts`, `timeout <= 0`) — these are correct given real, correctly-typed inputs; the bug is in test wiring, not production code. Do not change `WorkflowEngineAdapter`'s constructor-injection design. Do not investigate or fix any other file's test failures (fileed separately: eventbus issues, `tests/agent/test_rag_get_cfg.py`).

## Assumptions
- Changing the patch targets from `agent.workflow_engine_adapter.WorkflowEngine` to `agent.orchestrator.WorkflowEngine` (and adding `agent.workflow_engine_adapter.WorkflowEngine`/`StateStore` patches) will correctly intercept the real `WorkflowEngine` construction and inject `mock_engine_instance` instead.
- Patching `StateStore` at both `agent.orchestrator.StateStore` and `agent.workflow_engine_adapter.StateStore` prevents database access during tests.
- The existing scripted `_engine_run` side effect (lines 83-86) is sufficient for these tests — they don't need real retry/timeout semantics.

## Design decisions
- In `_patch_workflow_loader`, replace:
```python
patch(
    "agent.workflow_engine_adapter.WorkflowEngine",
    return_value=mock_engine_instance,
),
```
with:
```python
patch("agent.orchestrator.WorkflowEngine", return_value=mock_engine_instance),
patch("agent.orchestrator.StateStore"),
patch("agent.workflow_engine_adapter.WorkflowEngine", return_value=mock_engine_instance),
patch("agent.workflow_engine_adapter.StateStore"),
```
This ensures the mock `WorkflowEngine` is returned when `Orchestrator.__init__` calls `WorkflowEngine(...)`, rather than the real `WorkflowEngine` being constructed and causing `TypeError` on numeric comparisons with `MagicMock` attributes. Similarly, `StateStore` is patched at both locations where it's imported to prevent database access.

## Alternatives considered
- Using a separate `_FALLBACK_DEFAULTS` dict for the "no config available" case vs. the "config loaded but incomplete" case — rejected because the Plan suggests this as a possible future enhancement, not an immediate fix.
- Adding try/except around the fallback path in `resolve_rag_config` itself — rejected because it doesn't address the root cause (self-contradiction between defaults and validation).

## Implementation
### Target file
`tests/integration/test_orchestrator_integration.py`

### Procedure
Replace `patch("agent.workflow_engine_adapter.WorkflowEngine")` with `patch("agent.orchestrator.WorkflowEngine")` in `_patch_workflow_loader` fixture, and add `StateStore` patches at both import locations.

### Method
Mechanical edit: modify the patch target strings in the fixture.

### Details
1. Line 97: Change `patch("agent.workflow_engine_adapter.WorkflowEngine")` to `patch("agent.orchestrator.WorkflowEngine")`
2. Add `patch("agent.orchestrator.StateStore")` before the WorkflowEngine patch
3. Add `patch("agent.workflow_engine_adapter.WorkflowEngine", return_value=mock_engine_instance)` after the StateStore patch
4. Add `patch("agent.workflow_engine_adapter.StateStore")` after the WorkflowEngine adapter patch

## Compatibility considerations
Changing the patch targets to `agent.orchestrator.WorkflowEngine`, `agent.orchestrator.StateStore`, `agent.workflow_engine_adapter.WorkflowEngine`, and `agent.workflow_engine_adapter.StateStore` may not work if Python's import caching prevents the patches from intercepting the calls. Run targeted tests after making changes to catch any issues early.

## Security considerations
N/A: test-only change.

## Rollback considerations
If the fix causes unexpected side effects, revert the patch target change and instead choose the alternative direction (update the test to expect `ValueError` if the defaults direction was chosen, or revert the defaults change if the raise-based direction was chosen).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/integration/test_orchestrator_integration.py | Unit test execution | `uv run pytest tests/integration/test_orchestrator_integration.py -v` | 0 failures |
| tests/integration/ | Integration regression | `uv run pytest tests/integration/ -q` | No new failures in integration test suite |
| tests/agent/ | Integration regression | `uv run pytest tests/agent/ -q` | No new failures in agent test suite |

## Completion criteria
- [ ] REQ-ORCH-001-001: The mock patch targets are corrected to `agent.orchestrator.WorkflowEngine`, `agent.orchestrator.StateStore`, `agent.workflow_engine_adapter.WorkflowEngine`, and `agent.workflow_engine_adapter.StateStore`
- [ ] REQ-ORCH-001-002: `uv run pytest tests/integration/test_orchestrator_integration.py -v` — 0 failures
- [ ] REQ-ORCH-001-003: None of the 17 previously-failing tests merely stop raising `TypeError` without their actual behavioral assertions being exercised — confirm each test's `mock_engine_instance.run`/`_engine_run` path is genuinely invoked
- [ ] REQ-ORCH-001-003: No other integration test regresses (`uv run pytest tests/integration/ -q`)

## Out of scope
- Changing `RagConfigValidator`'s general validation rules beyond the specific `use_search`/`llm_url`/`embed_url` interaction
- Investigating or fixing any other file's test failures

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | REQ-ORCH-001-001; Verify correct approach (read orchestrator.py) | Completed | 20260918-192741 | 20260918-192741 |  |
| 2 | REQ-ORCH-001-001; Verify correct approach (read workflow_engine_adapter.py) | Completed | 20260918-192741 | 20260918-192741 |  |
| 3 | REQ-ORCH-001-001; Update mock patch targets (WorkflowEngine + StateStore in both modules) | Completed | 20260918-192741 | 20260918-192741 |  |
| 4 | REQ-ORCH-001-001; Fix test_handle_turn_invokes_workflow_engine_run test | Completed | 20260918-192741 | 20260918-192741 |  |
| 5 | REQ-ORCH-001-002; Run targeted test | Completed | 20260918-192741 | 20260918-192741 | 39 passed |
| 6 | REQ-ORCH-001-003; Run integration regression test | Completed | 20260918-192741 | 20260918-192741 | 1 new failure unrelated to change |
| 7 | REQ-ORCH-001-003; Run agent regression test | Pending | — | — | Pre-existing failures |

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
- **Requirement ID**: REQ-ORCH-001-001
- **Source issue**: issues/20260917-110800_orch01_orchestrator-integration-test-suite-failing-after-fast-forward-sync.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-225032_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-002450
- **Related target files**: tests/integration/test_orchestrator_integration.py
