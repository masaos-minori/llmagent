## Goal

Issue an `ApprovalGrant` (new) for every call that passes the approval gate, bound to the prepared call so the gateway can verify it (`REQ-006` approval grant, AC-4).

## Scope
**Release unit**: auth-intent

## Assumptions
- Grant expiry is a fixed module constant (short-lived, single-use); no `agent.toml` key is added (Plan Assumption; UNK-01, owner decides at mcpdl003).
- `ApprovalGrant` (new) is defined by row 8 (`scripts/agent/shared/models.py`); within the unit, land row 8 before this row (verified 2026-11-20).

## Design decisions
- In `run_approval_checks` (line 202), build the grant after a call passes risk/plan-mode checks: tool name, sha256 of canonical-JSON args, execution mode, issued_at timestamp, expiry constant.
- `PreparedToolCall` is frozen; attach the grant with `dataclasses.replace` so downstream receives the grant-bound copy.
- Denied calls get no grant; denied ids keep the current return contract.

## Alternatives considered
- Storing grants in a side map keyed by call id: rejected — the gateway must verify the exact object bound to the call being executed; a map invites reuse.

## Implementation
### Target file
`scripts/agent/tool_approval.py`

### Procedure
Extend `run_approval_checks` to return grant-bound `PreparedToolCall` objects for approved calls; construct the grant with `ApprovalGrant` (new) at approval time. Companion edit (verification finding 2026-11-20): add the `grant: ApprovalGrant | None = None` field to `PreparedToolCall` in `scripts/agent/tool_preparation.py` — a frozen dataclass cannot gain a field via `dataclasses.replace`, so the field addition is part of this row.

### Method
Compute the args hash with `shared.json_utils.dumps` canonical form (already imported, line 14 region); compare nothing here — verification happens only at the gateway (row 3).

### Details
- The module-level expiry constant lives in this module until the mcpdl003 config decision.
- Grant issuance covers every approved call including READ calls only when a grant is required downstream; non-READ calls always get one.

### Companion test files
- `tests/agent/test_tool_approval_preflight.py`
  - Procedure: add cases — approved call carries a grant with matching tool/args hash; denied call carries none; grant expiry constant honored.
  - Validation: `uv run pytest tests/agent/test_tool_approval_preflight.py` passes.

## Compatibility considerations
`run_approval_checks` return type keeps `(approved_calls, denied_ids)`; the approved objects gain the grant field only.

## Security considerations
Grant binds tool + args hash + mode at approval time; the gateway rejects any later mismatch (AC-4). Server-side validation stays independent (ADR-012 INV-04).

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_tool_approval_preflight.py tests/agent/test_repository_gateway.py` — grant present exactly on approved calls.

## Completion criteria
Every approved non-READ `PreparedToolCall` reaches execution carrying a single-use grant whose tool/args-hash/mode match the approval decision.

## Out of Scope
Grant verification in `_gate_write` (row 3); grant model definition (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | `run_approval_checks` issues grants via `_issue_grant` + `dataclasses.replace`; `_GRANT_TTL_SECONDS = 300.0` module constant. Deviation from Method: the args hash reuses `tool_preparation._canonical_args_hash` (the exact function behind `ToolExecutionContext.args_hash`) instead of `shared.json_utils.dumps` — orjson (raw UTF-8) and `json.dumps` (ensure_ascii default) differ on non-ASCII args, and the gateway comparison must hash identically. Grant issued only for approved non-READ calls (READ stays grant-less per Details). Companion edits landed: `PreparedToolCall.grant` field; `audit_approval`/`check_approval` gained an `idempotency_key` parameter so approval events carry the logical call id (REQ-008/AC-2, fills the value pinned by row 22). |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | `TestApprovalGrantIssuance` added (6 tests): interactive grant fields (tool/args_hash/mode/TTL), auto mode, READ grant-less, denied grant-less, tamper/rebind breaks hash match, approval event carries logical call id. New tests pin `ctx.conv.plan_mode = False` (MagicMock fixture is truthy). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff clean; mypy scripts/ clean (445 files); lint-imports 6 kept; tests/agent + tests/shared: 5792 passed, 3 skipped. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-21 | N/A: docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/agent/tool_approval.py`, `scripts/agent/tool_preparation.py` (companion `grant` field), `tests/agent/test_tool_approval_preflight.py`
