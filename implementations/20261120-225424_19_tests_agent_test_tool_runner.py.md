## Goal

Remove the transport-key assertions and add the fail-closed state/audit and intent-transition tests for `tool_runner` (`REQ-003` key removal, `REQ-005` transitions, `REQ-007` fail-closed, `REQ-009` stale handling).

## Scope
**Release unit**: contract-chain (key-assertion removal, Phase 1/3). The fail-closed transition tests land with unit auth-intent.

## Assumptions
- Phase 1 requires these tests to be added failing-first (issue instruction: tests before the grant and fail-closed code).

## Design decisions
- Delete the derive-key assertions at :2325, :2343, :2366, :2547, :2551, :2564 and any fixture that builds `_state_key`-shaped expectations.
- Add characterization tests: recorder write failure denies a side-effecting call but not a read-only one; mandatory-audit failure denies; intent transitions appear in order `pending` → `dispatch_starting` (new) → `dispatched` → `response_received` (new) → `completed`/`failed`; a post-send transport failure leaves the row dispatch-stage for stale classification.
- Recorder fakes must match the row 6 protocol (logical call id keyed).

## Alternatives considered
- N/A: the row mirrors the Plan's Phase 1 test inventory.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
Delete the six key-assertion sites; add the fail-closed and transition regression tests; update fakes to the new recorder signature.

### Method
Characterization tests first (red until rows 4-12 land within the same release unit).

### Details
- Include a no-internal-id check: no tool message or denial text emitted by the runner contains a key/id string beyond the opaque call id.

## Compatibility considerations
`tests/agent/test_tool_loop_guard_wiring.py` and `tests/agent/test_agent_repl_tool_exec.py` monkeypatch the gate wiring and stay untouched (Plan consumer-scan disposition).

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_tool_runner.py` — green once the unit's code rows land; new denials pinned.

## Completion criteria
No test references `_idempotency_key`, `_state_key`, or derived-key shapes; every Plan-enumerated newly failing path has a pinning test.

## Out of Scope
Gateway-bypass tests (row 3's companion); audit-internal tests (row 5's companion).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only |

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
- **Requirement ID**: `REQ-003`, `REQ-005`, `REQ-007`, `REQ-009`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `tests/agent/test_tool_runner.py`
