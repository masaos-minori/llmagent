## Goal
Add one test that drives `RagPipeline.augment()` through an HTTP transient failure and asserts the in-process stages run in the order MQE, search, fusion, rerank (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit
Adds one test function to `tests/rag/test_rag_http_mode.py`. No production change.

## Assumptions
- The existing fallback test stubs `run` entirely, so it never observes stage order (verified: it replaces `pipeline.run` with an AsyncMock).
- Independent of the four ADR-editing procedures (Plan Phase 1); runs first among this Plan's documents.
- The fallback path opens the local database through `RagDatabaseConnection`, computes the local identity, applies `_identity_gate()`, then calls `self.run()`; the test patches the connection and identity helpers the way the neighboring fallback tests do.

## Design decisions
- Record stage order by patching the lifecycle stage runner (`_run_stage`) so each call appends the stage class name; do not stub `run`.
- Keep the transient failure produced by the patched `call_rag_service`, as in the neighboring test, so the real fallback branch executes.

## Alternatives considered
N/A: stubbing `run` was rejected because it hides the order under test.

## Implementation
### Target file
`tests/rag/test_rag_http_mode.py`

### Procedure
1. Read the neighboring fallback test and copy its pipeline construction and patches.
2. Add `test_in_process_fallback_runs_stages_in_order`(new): patch `call_rag_service` to return a transient failure, patch the lifecycle `_run_stage` with a recorder, call `augment()`, and assert the recorded stage names equal the expected order for the four pre-augment stages.
3. Assert the augment stage still runs after them if the recorder can observe it; otherwise assert only the four stages and say so in the docstring.

### Method
Add a pytest async test using `monkeypatch`/`patch` and a list recorder; no new fixtures.

### Details
- Use `RagPipelineStageLifecycle` names from `scripts/rag/stage_lifecycle.py`; do not hard-code line numbers.
- Do not weaken or edit existing assertions.

## Compatibility considerations
Test-only addition.

## Security considerations
N/A: test-only change; no production code, secret, or permission behavior changes

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py -q`: pass
- Mutation check: temporarily swap two stages in the lifecycle and confirm the new test fails, then restore.
- `uv run ruff check tests/rag/test_rag_http_mode.py` and `uv run mypy tests/rag/test_rag_http_mode.py` as required by `rules/toolchain.md`

## Completion criteria
- The new test fails if the stage order changes and passes on the current code.
- Existing tests in the file are unchanged and pass.

## Out of Scope
- Production code changes.
- Verification text in ADR-010 (a later procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or change the test as described in Implementation > Procedure | Completed | 20261108-113844 | 20261108-113844 | — |
| 2 | Run the test file, the mutation check, and lint and type checks | Completed | 20261108-113844 | 20261108-113844 | ruff/format/mypy/lint-imports pass; mutation check failed as expected then restored; full suite 7716 passed, 1 unrelated failure (tests/mcp_servers/mdq/test_mdq_health_posture.py, allowed_dir_invalid in this environment, no source touched); diff-cover N/A (no source change) |

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
- **Requirement ID**: `REQ-002` (fallback stage-order test)
- **Source issue**: issues/20261107-050705_adrver001_align-invariant-verification-claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-092352_adrver001_align-invariant-verification-claims.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111637
- **Related target files**: `tests/rag/test_rag_http_mode.py`
