## Goal

Remove the redundant posture-failure restatement from ADR-002's Startup Validation section and replace it with a one-line pointer to ADR-004, so ADR-002 no longer restates posture handling that ADR-004 already governs.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-004 is the single normative authority for how a `FAILED` posture result is handled; ADR-002 must point to it, not restate the abort.
- The redundant text is the Startup Validation bullet at L239 ("...a `FAILED` check aborts Agent startup"). Other ADR-002 locations already reference ADR-004 correctly (Target Environment Profile, the "no environment-specific downgrade" consequence, and the related-ADR list), so this row touches only the one bullet.
- The overlap with adrrev009 on `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` does not touch ADR-002; compatible, non-overlapping.
- The edit stays within the single Startup Validation bullet; all other ADR-002 text stays byte-identical.

## Design decisions
- Replace the posture bullet with a single pointer sentence to ADR-004 rather than deleting the Startup Validation section: the section still lists the config-existence and config-validity checks, and ADR-004 owns the posture-handling half.
- Keep the pointer phrasing intent-only (no exit-status or `required` values).

## Alternatives considered
- N/A: single-bullet replacement; no design space worth recording.

## Implementation
### Target file
`docs/10_adr/adr_02_01_002_platform-config-isolation.md`

### Procedure
1. Open ADR-002 and locate the "### Startup Validation" section.
2. Replace the posture bullet ("Whether each MCP server's own validation produced a posture with no `FAILED` check: ... a `FAILED` check aborts Agent startup") with one line pointing to ADR-004 for posture handling.
3. Leave the other Startup Validation bullets and all other sections unchanged.

### Method
- Locate the "### Startup Validation" heading.
- Edit the single posture bullet in place; keep the two config-check bullets above it.
- Match the surrounding bullet voice.

### Details
- Current bullet (Startup Validation): "Whether each MCP server's own validation produced a posture with no `FAILED` check: the Agent reads the postures published on each server's `GET /health` through `check_readiness()`, and a `FAILED` check aborts Agent startup."
- The replacement should say that each server's published Security Posture is validated at startup and that its handling is defined by ADR-004, without restating the abort or reading `check_readiness()` internals.
- Do not remove or alter the config-existence / config-validity bullets, which are not posture handling.

## Compatibility considerations
- N/A: single-ADR wording change; reinforces the ADR-004 pointer already present elsewhere in ADR-002.

## Security considerations
- Prose-only consolidation; the enforced fail-closed behavior is unchanged in code. State intent, not config values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Structural + invariant preservation: `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` against `HEAD`; confirm no invariant, reference, test citation, Known Deviation, or Approval text changed outside the single bullet.
- Cross-domain claim consistency: `uv run python tools/check_docs_consistency.py --domain mcp`.
- Japanese-text policy: `uv run python tools/check_docs_japanese.py` (English only).

## Completion criteria
- ADR-002 Startup Validation no longer restates the posture abort; it points to ADR-004 instead.
- `check_adr_structure.py`, `check_adr_preservation.py`, `check_docs_consistency.py --domain mcp`, and `check_docs_japanese.py` pass.

## Out of Scope
- Changing ADR-004, ADR-003, ADR-007, ADR-014 (covered by their own rows).
- Adding a distinct subprocess exit status or structured log line (code change out of scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-095915 | 20261111-095915 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-095915 | 20261111-095915 | check_adr_structure.py pass; check_adr_preservation.py exit 0 (warning: ADR-002 Startup Validation bullet wording change, mapped in commit); check_docs_consistency.py --domain mcp pass; check_docs_japanese.py pass |

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
- **Requirement ID**: `REQ-002` — stop restating posture handling in ADR-002 and point to ADR-004
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-225014_adrrev007_posture-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-065828
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`