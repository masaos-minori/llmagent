## Goal
Make `test_stage_order_with_mocked_stages` assert the stage order its name states (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit
Edits one existing test in `tests/rag/test_stage_lifecycle.py`; keeps its current assertion.

## Assumptions
- The test currently asserts only `isinstance(result, PipelineRunResult)` while `_run_stage` is patched (verified by reading the test).
- Independent of the ADR-editing procedures.

## Design decisions
- Assert the sequence of stage class names passed to the patched `_run_stage`, in addition to the existing type assertion.
- Do not change production code.

## Alternatives considered
N/A: strengthening the existing test is the Plan decision.

## Implementation
### Target file
`tests/rag/test_stage_lifecycle.py`

### Procedure
1. In the test, read `mock_run_stage.call_args_list`, extract each call's first argument stage class name, and assert the list equals MQE, search, fusion, rerank stage names in order.
2. Keep `assert isinstance(result, PipelineRunResult)`.

### Method
Use `call_args_list` of the existing patch; no new fixture.

### Details
- The expected names are the stage classes constructed in `RagPipelineStageLifecycle.run()`; read them from the source rather than hard-coding from memory.
- Augment is run outside `_run_stage`, so it is not in the list.

## Compatibility considerations
Test-only change; a stricter assertion.

## Security considerations
N/A: test-only change; no production code, secret, or permission behavior changes

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/rag/test_stage_lifecycle.py -q`: pass
- Mutation check: swap two stages in the lifecycle and confirm the test fails, then restore.
- `uv run ruff check` and `uv run mypy` on the file

## Completion criteria
- The test asserts the full order and passes; the former assertion is retained.

## Out of Scope
- Other tests in the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or change the test as described in Implementation > Procedure | Pending | — | — |  |
| 2 | Run the test file, the mutation check, and lint and type checks | Pending | — | — |  |

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
- **Requirement ID**: `REQ-002` (strengthen lifecycle stage-order test)
- **Source issue**: issues/20261107-050705_adrver001_align-invariant-verification-claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-092352_adrver001_align-invariant-verification-claims.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111637
- **Related target files**: `tests/rag/test_stage_lifecycle.py`
