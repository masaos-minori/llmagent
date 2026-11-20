## Goal

Pin that the outbound `X-Idempotency-Key` carries the opaque logical id and remove the derivation tests (`REQ-003` transport key replacement, AC-1, AC-3).

## Scope
**Release unit**: contract-chain

## Assumptions
- Row 26's code counterpart is row 16 (`http_transport.py`); tests are added failing-first per Phase 1.

## Design decisions
- Delete the `derive_idempotency_key` import (:22) and every derivation pin: the block at :252-291, the cross-transport identical-key test at :297-346 (including the subprocess pin at :332-333 and the local compare at :346), and the wfaudit002 HEAD_KEY literal pin class at :447-476. Verification finding 2026-11-20: the document previously cited only ":255-289 plus isolated :332" — the true deletion/rewrite scope is these three blocks.
- Add cases: two calls with identical args send different header values; a retry of one call re-sends the identical value; a call with no context is refused before any HTTP request (AC-3); the header matches the context's `call_id` (AC-2 end-to-end pin).

## Alternatives considered
- N/A: test-only mirror of row 16.

## Implementation
### Target file
`tests/shared/test_http_transport.py`

### Procedure
Remove the derivation import/assertions; add the opaque-id and refusal cases against the existing transport mock harness.

### Method
Extend the current request-capturing fixtures; no new harness.

### Details
- Keep the server-shape pins for `X-Session-Id`/Authorization behavior unchanged.

## Compatibility considerations
Any helper in this file that builds derived keys for fixtures switches to fixed uuid7 strings.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/shared/test_http_transport.py`.

## Completion criteria
No test references `derive_idempotency_key`; header assertions pin the logical id and the no-id refusal.

## Out of Scope
Routing-layer removal (row 16's companion); executor forwarding (row 14's companion).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | rewritten: derivation/HEAD_KEY pins deleted; TestLogicalCallIdHeader adds identical-args-different-header, retry-reuse, header==call_id, no-context refusal; stage pins on raise-site tests |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff+28 passed as part of tests/shared (1280 passed) |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-21 | 2026-11-21 | N/A: test-only |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `tests/shared/test_http_transport.py`
