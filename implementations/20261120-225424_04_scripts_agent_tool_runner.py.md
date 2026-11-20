## Goal

Delete the `_idempotency_key`/`_state_key` derivations, propagate the execution context, enforce grant presence on the gateway-bypass path, and make state/audit recording fail-closed for side-effecting calls (`REQ-003` key removal, `REQ-005` intent transitions, `REQ-007` fail-closed, `REQ-009` post-send failure handling).

## Scope
**Release unit**: contract-chain (key-removal part, Phase 3). The fail-closed intent-recording part (Phase 5) lands in unit auth-intent.

## Assumptions
- Side-effect classification uses `ALL_SIDE_EFFECTING_TOOLS` from `shared.tool_constants` (Plan Design).
- The recorder contract change is defined by row 6 (`context.py`); new state names by rows 9-10.

## Design decisions
- Delete `_idempotency_key` (:137-145) and `_state_key` (:148-160); all recording uses `pc.context`'s logical call id.
- `_record_pending_state` (:175-191) and `_finalize_state` (:195-211): for side-effecting calls a recorder write failure raises (denial surface: tool-error row via `execute_one_tool_call`), instead of the current `logger.warning` + `return None`; read-only calls keep best-effort.
- Gateway-bypass branch (:237-246): non-READ calls without a grant/context never reach `tools.execute` — deny before the `check_preflight` fallback.
- Wrap `_execute_prepared_call` with intent transitions: `dispatch_starting` (new) before, `dispatched` after the transport call starts, `response_received` (new) on response, `completed`/`failed` at finalize; a post-send transport failure leaves `dispatched`/`response_received` (new) for stale classification (never retried here, AC-6).
- Keep the audit call (:298-309) passing the logical id; mandatory-audit errors propagate (row 5).

## Alternatives considered
- Keeping `_state_key` as a fallback when the context is missing: rejected — AC-3 forbids side effects without an id; a fallback re-creates today's collision bug.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
Remove both key derivation functions; rewire `_record_pending_state`, `_finalize_state`, `_execute_prepared_call` (:214-246), the audit block (:295-310), and `_record_transport_failure` (:249+) to the logical call id and the intent transitions.

### Method
Fail-closed gate: compute side-effect class once per call (`_classify_retry_class` region already classifies); branch fail-open/fail-closed on that class only.

### Details
- REQ-004: no internal id or key appears in any LLM-facing tool message or error text; denial text stays the existing policy-denied wording.
- `_run_approval_gate` (:561-576) itself stays the sole approval gate; grant presence is checked at execution and at the gateway.

## Compatibility considerations
`tests/agent/test_tool_runner.py` transport-key assertions (:2325, :2343, :2366, :2547, :2551, :2564) are removed in row 19 in the same unit.

## Security considerations
Fail-closed means today-silent recorder/audit degradations become visible denials for side-effecting calls only (Plan Risk 1, pinned by Phase 1 tests).

## Rollback considerations
N/A: revert the commit (no persisted schema change in this file).

## Validation plan
`uv run pytest tests/agent/test_tool_runner.py` — fail-closed paths raise; no transport-key references remain; then `uv run ruff check . && uv run mypy scripts/`.

## Completion criteria
No `_idempotency_key`/`_state_key` code or references remain; a side-effecting call is denied when the intent row or mandatory audit cannot be written; intent transitions appear exactly in the Plan's order.

## Out of Scope
Audit mandatory-raising inside `tool_audit.py` (row 5); recorder protocol definition (row 6); plain-REPL wiring (row 7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 3 part lands with unit contract-chain; Phase 5 part with auth-intent |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs sweep owned by mcpai012 |

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
- **Related target files**: `scripts/agent/tool_runner.py`
