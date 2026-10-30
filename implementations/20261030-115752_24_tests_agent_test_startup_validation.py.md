# Implementation Procedure: `tests/agent/test_startup_validation.py`

## Goal

Add the publication-order regression confirming the runtime registry is never published before the posture gate completes (AC-5: structural order asserted via the startup-validation flow; plan Phase 3).

## Scope

- `tests/agent/test_startup_validation.py`: one new test; existing tests (:82 onward, RAG-classification suite) untouched.
- Test-only: the plan verified the ordering already holds (`scripts/agent/startup_validation.py:114-120` posture collection precedes `runtime_tools` publication); this row locks it, it does not change flow.

## Assumptions

- Lightweight row: single test against the existing pipeline structure; mocks follow the file's existing fixture style (`check_services` is already exercised with mocked readiness/discovery in this file).
- If row 5 lands first, the mandatoriness stage participates in the same flow and the order assertions must still hold — write the test so it asserts the relative order of three call marks (mandatoriness check → posture collection → registry publication) with the mandatoriness mark tolerant to being absent only in a clearly labeled pre-row-5 window. Needs Confirmation: land with row 5 to avoid the tolerant window (recommended: write after row 5).

## Design decisions

- Order proof by recorded call sequence: patch `collect_server_postures`, the discovery service, and (post-row-5) `_check_component_mandatoriness` (new) (row 5's (new) function) with markers appended to a list; assert index(posture) < index(publication) and, once row 5 exists, index(mandatoriness) < index(publication).
- Assert via `ctx.services_required.runtime_tools` assignment timing, mirroring the real stage, not by line-number introspection (stale-safe).

## Alternatives considered

- N/A: test-only confirmation per plan Out-of-Scope ("ordering machinery ... test-only confirmation").

## Implementation

### Target file

`tests/agent/test_startup_validation.py`

### Procedure

1. New test `test_runtime_registry_published_after_posture_gate` (new) in the file's async style (`async def test_...` with the module's existing asyncio fixtures).
2. Mock discovery to return a sentinel registry; assert publication occurs only after the posture mock returned and no fatal was recorded.

### Method

monkeypatch/`unittest.mock` markers; no sleeps or timing assumptions.

### Details

- The test documents AC-5 permanently; a future reorder in either this plan's or ragcorpus001's edits to `startup_validation.py` trips it (cross-plan guard given the recorded overlap on that file).

## Compatibility considerations

- N/A beyond fixture-style consistency with the existing file.

## Security considerations

- N/A: locks the fail-closed ordering property.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_startup_validation.py`; part of plan Phase 3 "Done when" (`tests/agent/test_production_config_validator.py` and this file).

## Completion criteria

- The regression passes and fails loudly if publication is ever moved before the posture gate (plan AC-5).

## Out of Scope

- All pipeline code changes (row 5); validator unit tests (row 23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the order-regression test | Pending | — | — | Recommended after row 5 |
| 3 | Run the file + `tests/agent` | Pending | — | — | |

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
- **Requirement ID**: AC-5 (registry never published before posture evaluation; test-only confirmation)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `tests/agent/test_startup_validation.py`
