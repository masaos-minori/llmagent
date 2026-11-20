## Goal

Correct the fail-closed row for `allowed_tools` to be mode-aware in the trust-boundaries table (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 157 lists `allowed_tools=[]` as a fail-closed gate that denies every tool unconditionally.

## Design decisions
- Qualify the fail-closed row at line 157: `allowed_tools=[]` is fail-closed under `explicit_allowlist`; under `discovered` an empty list is valid (base visibility applies).

## Alternatives considered
- Deleting the row: rejected because the empty-list fail-closed case still exists under `explicit_allowlist`.

## Implementation
### Target file
`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure
Edit the trust-boundary table row at line 157 to qualify the empty-list fail-closed claim by mode.

### Method
Append a mode qualifier to the row.

### Details
- Line 157: `allowed_tools=[]` fail-closed under `explicit_allowlist`; valid under `discovered`.

## Compatibility considerations
Documentation accuracy only; no behavior change.

## Security considerations
No security impact: wording matches the enforced fail-closed behavior under `explicit_allowlist`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run the doc checker named in `routing.md` after editing.

## Completion criteria
The fail-closed row is mode-aware; the doc checker passes.

## Out of Scope
Runtime enforcement (`runtime_tool_registry.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-193300 | 20261120-193300 | Edited `docs/91_security/security_01_architecture-and-trust-boundaries.md` line 157 trust-boundary table row: qualified the fail-closed claim to `explicit_allowlist` (denies every tool, including after reload) and added that it is valid (base visibility) under `discovered`; replaced the stale "production-validator error at load" note with the current reality (`validate_allowed_tools` accepts empty list; mode semantics in `shared/runtime_tool_registry.py` `apply_policy`). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-193300 | 20261120-193300 | Doc accuracy only; no behavior change. check_docs_quality/structure/content_policy(--strict) all pass; check_docs_consistency --domain agent reports only a pre-existing unrelated warning in agent_14 (not the edited file). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `docs/91_security/security_01_architecture-and-trust-boundaries.md`
