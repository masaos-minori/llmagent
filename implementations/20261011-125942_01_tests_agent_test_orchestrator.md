# Implementation Procedure: tests/agent/test_orchestrator.py

## Goal

Add an INV-02 regression test for ADR-014: verify that the Orchestrator creates exactly one shared LlmTurnExecutor instance.

## Scope

- `tests/agent/test_orchestrator.py`: Add a test case asserting single LlmTurnExecutor ownership.

## Assumptions

- The Orchestrator class and LlmTurnExecutor class exist and can be instantiated in tests.
- The Orchestrator constructor accepts the same parameters as currently used in existing tests.
- ADR-014 INV-02 (line 158) requires centralized creation of LlmTurnExecutor instances.

## Design decisions

- Add a test that instantiates the Orchestrator and asserts a single shared LlmTurnExecutor instance.
- The test should verify that no duplicate LlmTurnExecutor instances are created or held by other components.

## Alternatives considered

1. Add the test to an existing test class in `test_orchestrator.py` — preferred because the file already covers Orchestrator behavior.
2. Create a new test file — rejected because `test_orchestrator.py` already exists and is the canonical location for Orchestrator tests per ADR-014 Implementation References.

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. Add a test method to the existing test class in `test_orchestrator.py`.
2. Instantiate the Orchestrator using the same fixture pattern as existing tests.
3. Assert that `orchestrator._llm_executor` is a single LlmTurnExecutor instance.
4. Verify no other component holds a separate LlmTurnExecutor instance.

### Method

Unit test — instantiate the Orchestrator and inspect its internal state.

### Details

1. **Add INV-02 regression test (REQ-001)**:
   - Current code (`orchestrator.py:119`): `self._llm_executor = LlmTurnExecutor(...)` is the only instantiation site.
   - Add a test method (e.g., `test_orchestrator_single_llm_turn_executor`) that:
     - Instantiates the Orchestrator via the existing fixture pattern.
     - Asserts `isinstance(orchestrator._llm_executor, LlmTurnExecutor)`.
     - Asserts that `_llm_executor` is not None and is a single shared instance.
   - Reference: ADR-014 INV-02 (line 158) — "Creation of LlmTurnExecutor instances is centralized in the one component that actually drives the LLM/Tool Call round-trip loop."
   - Evidence: ADR-014 Verification section (line 165) states "no such test exists"; tracked as AGENT-002.

## Compatibility considerations

- The test accesses `orchestrator._llm_executor`, which is a private attribute. This is acceptable for a regression test verifying INV-02.
- If the Orchestrator constructor signature changes (e.g., due to workflow-fail-closed changes), the test may need parameter updates.

## Security considerations

N/A — this is a unit test for an invariant, not a security boundary change.

## Rollback considerations

- Reverting the test removes the regression guard for INV-02; the defect would be undetectable by automated testing again.
- No production code change — rollback is safe (just remove the test).

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| test_orchestrator.py | Unit: verify INV-02 test passes | `uv run pytest tests/agent/test_orchestrator.py -v` | Test passes |
| test_orchestrator.py | Lint/type: ruff, mypy | `uv run ruff check`, `uv run mypy --no-namespace-packages` | No lint/type errors |

## Completion criteria

- [ ] Test verifies Orchestrator creates exactly one LlmTurnExecutor instance (REQ-001).
- [ ] Test passes when run in isolation.
- [ ] ruff and mypy pass with no errors.

## Out of scope

- Changes to the Orchestrator constructor or LlmTurnExecutor interface.
- Tests for other INV-02 scenarios (e.g., concurrent access).
- Changes to non-Orchestrator components.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261012-081139 | 20261012-081139 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261012-081139 | 20261012-081139 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261012-081139 | 20261012-081139 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No docs/00_index.md mapping for this file |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20261007-154050_regtest01_add-inv-02-regression-test-and-keep-original-japanese-text-on-empty-normalization.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-164920_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-125942
- **Related target files**: `tests/agent/test_orchestrator.py`