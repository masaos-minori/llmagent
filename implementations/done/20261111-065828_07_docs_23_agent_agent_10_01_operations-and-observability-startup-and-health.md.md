## Goal

Point `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` at ADR-004 for the security-posture gate's failure behavior so the readiness severity note describes posture intent, the fail-closed abort, and the unverifiable case without restating the Safety/Integrity-vs-Availability classification or copying config values, while preserving the doc's operational severity model and the Manual Recovery section that another plan owns.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-004 is the single normative authority for how a `FAILED` posture result is handled; it aborts Agent startup regardless of `required` (fail-closed).
- The current readiness bullet (Line 74) restates the full posture classification (Safety/Integrity failure → FATAL regardless of `required`; Availability failure on a non-required server → WARNING; unreachable probe or unreadable `/health` → Availability) and already links to ADR-004 and `mcp_02_02`.
- Operational docs state intent, not exit-status codes or config values; the restated `McpServerConfig.required` condition and the Safety/Integrity-vs-Availability split collapse to a pointer to ADR-004.
- The overlap with adrrev009 on this file is compatible: this Plan edits the readiness/posture severity note (Line 74); adrrev009 rewrites the Manual Recovery steps (Lines 102-146). Different sections, no shared edit region; order them by the plans' sequence if both land.

## Design decisions
- In the readiness bullet (Line 74), keep that readiness covers every MCP server's Security Posture gate and that OK means every gate passed; replace the Safety/Integrity-vs-Availability classification and the `McpServerConfig.required` condition with a one-line pointer to ADR-004 covering intent, the `FAILED` fail-closed abort, and the unverifiable-probe case.
- Keep the doc's own FATAL/WARNING/SKIPPED/OK severity table and the `mcp_tool_discovery` ADR-004 pointer (Line 72) unchanged; only condense the posture-classification prose.

## Alternatives considered
- N/A: single-bullet condense; no design space worth recording.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Open the target doc.
2. Read ADR-004 (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`) to state the correct rule.
3. Condense the readiness bullet (Line 74): keep "readiness covers required-service availability and every MCP server's Security Posture gate" and that OK means every required service is available and every posture gate passed; replace the Safety/Integrity-vs-Availability restatement and the `McpServerConfig.required` reference with a pointer to ADR-004 (fail-closed; an unverifiable probe is treated as a failure).
4. Leave Manual Recovery (Lines 102-146) untouched.

### Method
- Locate the readiness bullet in the Important Notes list (Line 74).
- Collapse the posture classification into one pointer sentence; preserve the surrounding bullets and the severity table.
- Match the surrounding voice.

### Details
- Current OK definition (Line 66): "OK means every required service is available and every MCP server posture gate passed."
- Current readiness posture text (Line 74): "A required service that is unavailable, or a server whose posture gate reports a Safety or Integrity failure, is FATAL and aborts startup whatever `McpServerConfig.required` says; a non-required server whose gate failure is Availability is WARNING and startup continues. An unreachable probe or an unreadable `/health` body is an Availability failure. See [ADR-004](../10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md) and [mcp_02_02](../22_mcp/mcp_02_02_startup-modes-and-health.md)."
- adrrev009 edits Manual Recovery Steps (Lines 102-146), not Line 74.

## Compatibility considerations
- N/A: condenses the ADR-004 pointer already present at Line 74; does not touch the Manual Recovery section owned by adrrev009.

## Security considerations
- Prose-only consolidation; the enforced fail-closed behavior is unchanged in code. State intent, not config values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Cross-domain claim consistency: `uv run python tools/check_docs_consistency.py --domain agent`.
- Japanese-text policy: `uv run python tools/check_docs_japanese.py` (English only).

## Completion criteria
- The readiness note describes posture intent, the `FAILED` fail-closed abort, and the unverifiable case via a pointer to ADR-004, without restating the Safety/Integrity-vs-Availability classification or copying config values; the severity table and Manual Recovery section are unchanged.
- `check_docs_consistency.py --domain agent` and `check_docs_japanese.py` pass.

## Out of Scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-102229 | 20261111-102229 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-102229 | 20261111-102229 | check_docs_consistency.py --domain agent pass; check_docs_japanese.py pass; check_docs_structure.py pass |

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
- **Requirement ID**: `REQ-006` — describe posture failure behavior and the fail-closed guarantee at the operations level in `agent_10_01` without copying exit-status or config values
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source plan**: `plans/20261110-225014_adrrev007_posture-fail-closed.md`
- **Generated at**: 20261111-065828
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
