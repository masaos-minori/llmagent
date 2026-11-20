## Goal

Verify the approval grant immediately before `_gate_write` executes the call; deny on tool/argument/mode mismatch, expiry, or reuse (`REQ-006` gateway verification, AC-4).

## Scope
**Release unit**: auth-intent

## Assumptions
- The grant is carried on the `PreparedToolCall` and reaches the gateway through the caller-side call path updated by row 4 (`tool_runner.py`).
- `_denied_result` (used at :116) is the existing deny shape and stays the deny path.

## Design decisions
- `execute` (:82-96) and `_gate_write` (:98-127) accept the grant/context alongside `tool_name`/`args`; a write reaching the gateway without a valid grant is denied. (Citation fix 2026-11-20: the previously cited "lines 96-105" was off.)
- Verify immediately before `self._executor.execute` (:118): tool name match, sha256(args) equals the grant's args hash, execution mode match, expiry, and single use; mark the grant consumed after successful verification.
- Any mismatch returns `_denied_result(...)`; the gateway never prompts and never re-approves.

## Alternatives considered
- Verifying in `tool_runner` instead of the gateway: rejected — AC-4 requires the denial at the authorization boundary itself, so a direct gateway invocation is also covered.

## Implementation
### Target file
`scripts/agent/repository_gateway.py`

### Procedure
Add grant verification at the top of `_gate_write` (def at :98), before `check_preflight`; update `execute`'s signature (def at :82) to carry the grant.

### Method
Pure comparison against the grant fields; update the module docstring precondition (:62-68) to state that a grant must accompany non-READ calls.

### Details
- Keep the existing audit line (:120-122) and policy preflight order intact after the grant check.
- Reuse detection: the grant is single-use; a second verification of the same grant object fails.

### Companion test files
- `tests/agent/test_repository_gateway.py`
  - Procedure: add cases — direct gateway call with no grant denied; arguments changed after approval denied; wrong tool/mode denied; expired grant denied; grant reuse denied.
  - Validation: `uv run pytest tests/agent/test_repository_gateway.py` passes.

## Compatibility considerations
Callers must pass the grant; the only production caller is `tool_runner` (row 4), updated in the same release unit.

## Security considerations
This is the AC-4 boundary: an unapproved or tampered write cannot execute. Server-side git validation remains independent (ADR-012 INV-04).

## Rollback considerations
N/A: revert the commit (no persisted data changes).

## Validation plan
`uv run pytest tests/agent/test_repository_gateway.py` — grantless/mismatched/expired/reused calls denied via `_denied_result`.

## Completion criteria
`_gate_write` executes only when a fresh, matching grant is present; every denial path returns the existing denied result shape and is covered by a test.

## Out of Scope
Grant issuance (row 2); the gateway-bypass branch in `tool_runner` (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | `execute(ctx, tool_name, args, grant=None)`; `_verify_grant` checks tool match, args_hash vs `ToolExecutionContext.args_hash`, mode in `_GRANT_VALID_MODES` (AUTO/APPROVED), expiry, single-use via `_consumed_grants` (pruned at 1024). Denial → `_denied_result("Grant denied: ...")` with `error_type="denied"`, raised before `check_preflight`. Grant hash compares against the runner's canonical hash (tool_preparation._canonical_args_hash), not orjson dumps. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | `tests/agent/test_repository_gateway.py`: `_grant` fixture + `TestGrantVerificationAtGateway` (7 tests: pass, tool mismatch, args mismatch, mode mismatch, expired, single-use replay, missing grant on write). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | Targeted: gateway file 16 passed; full tests/agent+tests/shared batch run green (see batch record). ruff/mypy clean on the changed files. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-21 | Docs sweep owned by mcpai012 |

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
- **Related target files**: `scripts/agent/repository_gateway.py`, `tests/agent/test_repository_gateway.py`
