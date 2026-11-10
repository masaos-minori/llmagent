## Goal

Point `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` at ADR-004 for the pre-bind security-posture gate so the doc describes posture intent, fail-closed failure behavior, and the unverifiable-probe case without copying exit-status or config values, while keeping the `tool_definitions_strict` behavior intact.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-004 is the single normative authority for how a `FAILED` posture result is handled; it aborts Agent startup regardless of `required` (fail-closed).
- The current doc describes the `tool_definitions_strict` check and the per-server `required` discovery-failure handling but does not describe the pre-bind posture gate; its only ADR-004 mention is the required/non-required discovery rule at Line 45.
- Operational docs state intent, not exit-status codes or config values; the new prose must not copy TOML keys, exit-status strings, or code paths.
- The overlap with adrrev009 on `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` does not touch this file; compatible, non-overlapping.

## Design decisions
- Add one concise subsection after the discovery-failure-handling bullets (ending near Line 49) that names ADR-004 as the authority for the pre-bind posture gate: intent (every server's security posture positively confirmed before binding), failure behavior (`FAILED` aborts startup regardless of `required`, fail-closed), and the unverifiable case (a probe that cannot confirm posture is treated as `FAILED`). Keep the `tool_definitions_strict` table, status definitions, and `ProductionConfigValidator` note unchanged.
- Prose only; no TOML keys, no exit-status strings, no import or code-path copying.

## Alternatives considered
- N/A: single-subsection pointer; no design space worth recording.

## Implementation
### Target file
`docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`

### Procedure
1. Open the target doc.
2. Read ADR-004 (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`) to state the correct rule before writing.
3. After the discovery-failure-handling bullet list (ends Line 49), add a short subsection naming ADR-004 as the authority for the pre-bind posture gate: intent, the `FAILED` fail-closed abort (regardless of `required`), and the unverifiable-probe case. Do not copy exit-status or config values.
4. Leave the `tool_definitions_strict` table, the WARNING/FATAL/SKIPPED status definitions, and the `ProductionConfigValidator` note unchanged.

### Method
- Locate the Discovery failure handling section (Line 43) and its per-server bullet list (Lines 47-49).
- Insert the new subsection after Line 49, before the `ProductionConfigValidator` paragraph (Line 61); keep blank-line separation consistent with the surrounding sections.
- Match the surrounding voice; keep it to a few bullets.

### Details
- Current ADR-004 mention (Line 45): "MCP discovery follows the ADR-004 rule: an unavailable required server aborts startup; an unavailable non-required server is disabled and startup continues." This is the required/non-required discovery rule, not the posture gate; the new subsection covers the separate pre-bind gate.
- The doc currently names no posture-gate function; the gate runs pre-bind and is enforced in code, referenced here by authority (ADR-004) rather than by code path.

## Compatibility considerations
- N/A: additive subsection; reinforces the ADR-004 authority already cited for discovery at Line 45.

## Security considerations
- Prose-only consolidation; the enforced fail-closed behavior is unchanged in code. State intent, not config values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Cross-domain claim consistency: `uv run python tools/check_docs_consistency.py --domain mcp`.
- Japanese-text policy: `uv run python tools/check_docs_japanese.py` (English only).

## Completion criteria
- The doc describes posture intent, the `FAILED` fail-closed abort, and the unverifiable-probe case via a pointer to ADR-004, without copying exit-status or config values; the `tool_definitions_strict` behavior is unchanged.
- `check_docs_consistency.py --domain mcp` and `check_docs_japanese.py` pass.

## Out of Scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` — describe posture intent, failure behavior, and the unverifiable case in `mcp_06_09` without copying exit-status or config values
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source plan**: `plans/20261110-225014_adrrev007_posture-fail-closed.md`
- **Generated at**: 20261111-065828
- **Related target files**: `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`
