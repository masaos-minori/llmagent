## Goal

Create the test for ADR-001 INV-02: no call path reaches the tool-execution and LLM-turn chain except through the Workflow Engine (AAL-001).

## Scope
**Release unit**: N/A: not part of a release unit

One new test module, with the Plan's proposed scope (UNK-01): the tool-execution and LLM-turn chain; slash commands and MCP lifecycle start and stop are allowlisted. No production change.

## Assumptions

- Call sites today: `handle_llm_turn` only in `scripts/agent/workflow_engine_adapter.py:390`, `LLMTurnRunner(` only in `scripts/agent/llm_turn_executor.py:90`, `execute_all_tool_calls(` only in `scripts/agent/llm_turn_runner.py:160` (rg in Step 3a).
- The maintainer may amend the scope (Plan UNK-01); the allowlist is data in the test, so an amendment changes data only.

## Design decisions

- An AST scan of `scripts/` for call sites of the chain symbols against an explicit allowlist, asserting each allowlisted site is found (not vacuous).
- A behavioral test that `handle_llm_turn` runs only inside the engine run of `WorkflowEngineAdapter.execute_turn`.

## Alternatives considered

Grep-only scan: rejected, strings and comments cause false hits.

## Implementation
### Target file
`tests/agent/workflow/test_no_workflow_bypass.py` (new)

### Procedure
1. Read `tests/agent/workflow/test_adapter_guards.py` and `tests/agent/test_orchestrator.py::TestWorkflowLoadFailureIsFatal` for the adapter fixtures.
2. Create `tests/agent/workflow/test_no_workflow_bypass.py` (new).
3. Add the `repo_scan` AST test with the allowlist.
4. Add the behavioral test that a turn reaches `handle_llm_turn` only through the engine.

### Method
- Match `ast.Call` by attribute or name for `handle_llm_turn`, `LLMTurnRunner`, `execute_all_tool_calls`, and `.execute(` on the executor.
- Record the allowlist as `(relative path, symbol)` pairs with a reason each.

### Details
- Mutation check: add a direct `execute_all_tool_calls` call in another agent module temporarily, confirm failure, revert.
- Cite the tests in ADR-001's INV-02 row in procedure 10 and the index matrix in procedure 11.

## Compatibility considerations

N/A: adds a test only; no production behavior changes.

## Security considerations

N/A: no secret, permission, or input handling is touched; test fixtures use dummy tokens only.

## Rollback considerations

N/A: revert the commit (the file is new).

## Validation plan

- `uv run pytest tests/agent/workflow/test_no_workflow_bypass.py -q`
- ruff and mypy on the file

## Completion criteria

- Scan and behavioral tests pass and fail under the mutation.
- Only the new file was added.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.
- Slash-command and MCP lifecycle paths beyond the recorded allowlist.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Mutation-check the new test: break the invariant temporarily, confirm the test fails, revert the break | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (no bypass of the Workflow Engine (ADR-001 INV-02)), `REQ-008` (no production change, every test mutation-checked)
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-165432_gov006_restore-blocking-verification-rows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-165833
- **Related target files**: `tests/agent/workflow/test_no_workflow_bypass.py`
