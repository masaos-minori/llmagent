## Goal

Point `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` at ADR-004 for the security-posture gate's failure behavior per startup mode, removing the copied exit-status reference and condensing the refuse-to-bind restatement into a pointer, while keeping the `/health` `security` block field semantics.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-004 is the single normative authority for how a `FAILED` posture result is handled; it aborts startup regardless of `required` (fail-closed).
- The current `security` block prose (Lines 56-58) restates the posture failure behavior ("refuses to bind (exit status 1)", "`failed` check blocks Agent startup regardless of `required`") and already links to ADR-004.
- Operational docs state intent, not exit-status codes or config values; the "(exit status 1)" phrase must be removed.
- The posture gate applies to both `persistent` and `subprocess` startup modes via the common start path.

## Design decisions
- In the `security` block prose (Lines 56-58), remove the "(exit status 1)" phrase and collapse the refuse-to-bind restatement into a pointer to ADR-004 covering intent, the `FAILED` fail-closed abort (both startup modes), and the non-failing cases (`warning` posture is reported and the server still binds; `not_applicable` is never a failure).
- Keep the `security` block field table (Lines 46-54) and the `validated`/`ready`/`status` semantics unchanged.

## Alternatives considered
- N/A: single-prose condense; no design space worth recording.

## Implementation
### Target file
`docs/22_mcp/mcp_02_02_startup-modes-and-health.md`

### Procedure
1. Open the target doc.
2. Read ADR-004 (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`) to state the correct rule.
3. Remove "(exit status 1)" from the security-block prose (Line 56).
4. Condense the posture-failure sentences (Lines 56-58) into a pointer to ADR-004: intent (every server validates posture at startup and publishes it in the `/health` `security` block), the `FAILED` fail-closed abort regardless of `required` for both startup modes, and that a `warning` posture still binds while `not_applicable` is not a failure.
5. Leave the field table and Bearer Auth sections unchanged.

### Method
- Locate the `security` block prose (Lines 44, 56-58).
- Edit in place; preserve the field table and surrounding prose.
- Match the surrounding voice.

### Details
- Current field table (Lines 46-54): `contract_version`, `server_key`, `policy_version`, `validated`, `ready`, `fingerprint`, `checks`.
- Current Line 56: "...A server whose posture is not validated refuses to bind (exit status 1); the check runs in the common start path used by the Agent-launched binaries ... so no launch route skips it."
- Current Line 58: "The Agent reads this block during startup readiness and MCP tool discovery. A `failed` check blocks Agent startup regardless of the server's `required` classification; see [ADR-004](../10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md). A server whose posture is not validated refuses to bind its HTTP port."

## Compatibility considerations
- N/A: condenses the ADR-004 pointer already present at Line 58; keeps the `/health` `security` block field semantics intact.

## Security considerations
- Prose-only consolidation; the enforced fail-closed behavior is unchanged in code. State intent, not config values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Cross-domain claim consistency: `uv run python tools/check_docs_consistency.py --domain mcp`.
- Japanese-text policy: `uv run python tools/check_docs_japanese.py` (English only).

## Completion criteria
- The `security` block prose describes posture intent, the `FAILED` fail-closed abort, and the non-failing cases via a pointer to ADR-004, without copying the exit-status or config values; the field table and Bearer Auth sections are unchanged.
- `check_docs_consistency.py --domain mcp` and `check_docs_japanese.py` pass.

## Out of Scope
- Changing the `/health` `security` block field definitions or the Bearer Authentication section.
- Adding a distinct subprocess exit status or structured log line (code change out of scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-102229 | 20261111-102229 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-102229 | 20261111-102229 | check_docs_consistency.py --domain mcp pass; check_docs_japanese.py pass; check_docs_structure.py pass |

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
- **Requirement ID**: `REQ-006` — describe posture intent, failure behavior, and the unverifiable case per startup mode in `mcp_02_02` without copying exit-status or config values
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-225014_adrrev007_posture-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-065828
- **Related target files**: `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
