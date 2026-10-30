# Implementation Procedure: test_tool_transport_invoker.py hint attachment tests

## Goal

Assert hints are attached exactly on UNAVAILABLE and HALF_OPEN-busy rejections and absent
elsewhere in `tests/shared/test_tool_transport_invoker.py` (REQ-002).

## Scope

**In scope:**
- `tests/shared/test_tool_transport_invoker.py`: new tests for hint presence/shape on
  invoker results.

**Out of scope:**
- `tests/shared/test_tool_transport_invoker_merge.py` (separate merge-behavior suite,
  characterization only — must stay green untouched).

## Assumptions
- Verified at HEAD `124e340b4`: file exists with 26 tests covering health/lifecycle/
  semaphore/recording via `AsyncMock`/`MagicMock` transports and a real
  `McpServerHealthRegistry`. Test-first: new assertions fail until row 03 lands.

## Design decisions
- New tests:
  - UNAVAILABLE rejection: drive registry to UNAVAILABLE (3 failures), invoke, assert the
    returned `ToolCallResult.availability_hint.reason == "server_unavailable"`,
    `circuit_state == UNAVAILABLE`, `retry_after_seconds` (new) is an int in `[0, 30]`, and the
    legacy message text is unchanged.
  - HALF_OPEN-busy: transition to HALF_OPEN, acquire the trial externally, invoke, assert
    `reason == "half_open_trial_in_progress"`, `circuit_state == HALF_OPEN`,
    `retry_after_seconds is None`, legacy text unchanged.
  - Absence: healthy call → `availability_hint is None`; tool-error result (server
    is_error body) → `None`; transport-failure result (`TransportError` path) → `None`.
- Reuse the file's existing registry/fixture helpers rather than new scaffolding.

## Alternatives considered
- Snapshot-comparing the whole result dataclass: rejected — field-level asserts match the
  suite's existing style and won't churn on unrelated field additions.

## Implementation
### Target file
`tests/shared/test_tool_transport_invoker.py`

### Procedure
1. Keep all 26 existing tests byte-identical.
2. Append the hint-presence/absence tests described above.

### Method
- Same mock-transport patterns as existing tests (`AsyncMock` on
  `HttpTransport.call`, real registry).

### Details
- Cooldown boundaries are mocked via a registry constructed with
  `half_open_cooldown_sec` and `time.monotonic` patching, mirroring
  `tests/shared/test_mcp_health.py` patterns.

## Compatibility considerations
- The exact legacy rejection strings are asserted here — this file is the contract owner
  for "free text preserved" (plan Design).

## Security considerations
- Not applicable (test-only).

## Rollback considerations
- Delete the appended tests to revert.

## Validation plan
- `uv run pytest tests/shared/test_tool_transport_invoker.py
  tests/shared/test_tool_transport_invoker_merge.py` — new tests fail before row 03,
  green after; merge suite green throughout.

## Completion criteria
- Presence on exactly the two health-gate outcomes and absence on healthy/tool/transport
  results all asserted and passing after row 03.

## Out of Scope
- Row 03 implementation, guard/runner tests (rows 10-11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append hint presence/absence tests (fail before row 03 lands) | Pending | — | — | |
| 2 | Confirm 26 existing tests and the merge suite byte-identical and green | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `tests/shared/test_tool_transport_invoker.py`
