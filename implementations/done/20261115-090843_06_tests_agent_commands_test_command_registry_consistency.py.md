## Goal

Ensure `test_command_registry_consistency.py` carries no stale static-count assertion and, if `REQ-005` extends runtime-total coverage here, add it. (`REQ-005`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- **Needs confirmation (non-blocking):** the Plan's Background flags "which exact command tests assert the static count" as unresolved, and this row asks to "update any static-count assertion in the command-registry test." Adversarial verification found **no** static-tool-count assertion in `test_command_registry_consistency.py` today — it tests handler/MRO/completion consistency, not tool counts. So there is nothing to update unless a sibling row adds such an assertion.
- The primary `REQ-005` tests (registry totals, typed fail-closed error) belong in `test_cmd_mcp.py` (see that row); this row is a guard, not the main home.

## Design decisions
- Add a regression guard asserting this file contains no `cfg.tool.tool_definitions` count assertion, so a future regression is caught.
- Only add a positive runtime-total test here if the owner scopes `REQ-005` coverage to this file; otherwise leave it as the guard.

## Alternatives considered
- Inventing a new tool-count test here: out of scope — the natural home is `test_cmd_mcp.py`; adding one elsewhere without an owner decision would duplicate coverage.

## Implementation
### Target file
`tests/agent/commands/test_command_registry_consistency.py`

### Procedure
1. Verify (via `grep`) that this file has no `cfg.tool.tool_definitions` count assertion. If none exist, record that and skip any "update" step.
2. If a sibling row introduces a static-count assertion in this file, update it to the registry total (as in `test_cmd_mcp.py`).
3. Optionally, if the owner scopes `REQ-005` coverage here, add a runtime-total assertion; do not add one unscoped.

### Method
Check with `grep -n "tool_definitions" tests/agent/commands/test_command_registry_consistency.py`.

### Details
- The current test suite (handler existence, async/sync kind, MRO mixin counts, completion drift) does not touch tool counts; the guard in step 1 confirms this.

## Compatibility considerations
Test-only change; additive guard, no removal of existing consistency coverage.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
- Run `pytest tests/agent/commands/test_command_registry_consistency.py` green.
- Confirm no `cfg.tool.tool_definitions` count assertion remains.

## Completion criteria
- This file has no stale static-count assertion; any scoped `REQ-005` runtime-total coverage is present.

## Out of Scope
- The main registry-total / fail-closed tests (`test_cmd_mcp.py`, `REQ-005`).
- The `/help` count test (`registry.py`, `REQ-003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-184611 | 20261115-184611 | See Assumptions: no static-count assertion currently exists REQ-005 guard: grep confirms no cfg.tool.tool_definitions count assertion; no change needed |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no test change needed (guard-only, no static-count assertion exists) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-184611 | 20261115-184611 | no file changed; consistency test passes as-is |

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
- **Requirement ID**: `REQ-005` — command-registry test must carry no stale static-count assertion
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-090843
- **Related target files**: `tests/agent/commands/test_command_registry_consistency.py`