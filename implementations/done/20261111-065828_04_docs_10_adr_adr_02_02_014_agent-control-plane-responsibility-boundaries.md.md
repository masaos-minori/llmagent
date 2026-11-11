## Goal

Stop ADR-014 from restating what happens when a server's Security Posture is not accepted, and replace that failure-consequence framing with a one-line pointer to ADR-004, while preserving ADR-014's own responsibility-boundary content about who validates the posture contract and who gates Tool registration.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-004 is the single normative authority for the failure consequence of a not-accepted posture (startup abort); ADR-014 must point to it, not restate it.
- ADR-014 does NOT currently restate the abort rule. Its three posture mentions are: L60 (server publishes posture on `/health`), L66 (Agent gates Tool registration on the contract result), and the Automated Tests description at L138 ("no `RuntimeToolRegistry` entry for a server whose posture is not accepted"). None of them states the fail-closed abort.
- Distinguishing "posture handling" (the failure consequence, ADR-004's domain) from "responsibility boundary" (who validates the contract version/check-set/shape and who gates registration, ADR-014's topic) requires implementer judgment. Only the failure-consequence framing is converted; the validation-responsibility framing is kept.
- The registry-exclusion described at L138 is closely tied to ADR-003 Decision Detail #16 (row 1 of this Plan); the two must not drift after both edits.
- The overlap with adrrev009 on `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` does not touch ADR-014; compatible, non-overlapping.

## Design decisions
- Convert only the failure-consequence clause (L138's "no `RuntimeToolRegistry` entry for a server whose posture is not accepted") to a pointer to ADR-004; keep L60/L66's validation-responsibility framing intact.
- Point to ADR-004 for the failure consequence, and reference ADR-003 for the registry-exclusion mechanism where it still appears, so authority attribution stays correct.

## Alternatives considered
- N/A: narrow wording edit; no design space worth recording.

## Implementation
### Target file
`docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`

### Procedure
1. Open ADR-014.
2. In the Automated Tests table, rewrite the L138 row's description so it no longer restates the exclusion consequence as a fact; point the failure consequence to ADR-004 and keep the INV-03 reference and the two test citations.
3. Review L60 and L66. Keep the validation-responsibility framing (who validates the posture contract, who gates registration). If either restates the failure consequence (that a not-accepted posture aborts startup or excludes the server), convert only that clause to a pointer to ADR-004 and attribute the registry-exclusion to ADR-003.
4. Leave all other sections unchanged.

### Method
- Locate the Automated Tests table row citing `test_mcp_health_posture.py` / `test_runtime_tool_registry.py`.
- Locate the responsibility bullets at L60 and L66.
- Edit only the failure-consequence clauses in place; do not renumber bullets or reorder the tests table.
- Match the surrounding voice.

### Details
- Current L138 (Automated Tests): "Agent-side posture contract validation, and no `RuntimeToolRegistry` entry for a server whose posture is not accepted (contract gate only; the INV-03 duplication rule itself stays review-verified)".
- Current L66: "The Agent's MCP-security responsibility is limited to validating the common posture contract that each MCP server publishes (contract version, check set, and result shape) and gating Tool registration on that result."

## Compatibility considerations
- Coordinate with row 1 (ADR-003 Decision Detail #16): both rows touch the not-accepted-posture registry-exclusion concept; keep their attributions (ADR-003 for the exclusion mechanism, ADR-004 for the failure consequence) consistent.
- N/A otherwise: wording change within one ADR.

## Security considerations
- Prose-only consolidation; the enforced fail-closed behavior is unchanged in code. State intent, not config values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Structural + invariant preservation: `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` against `HEAD`; confirm no invariant, reference, test citation, Known Deviation, or Approval text changed outside the targeted clauses.
- Cross-domain claim consistency: `uv run python tools/check_docs_consistency.py --domain agent`.
- Japanese-text policy: `uv run python tools/check_docs_japanese.py` (English only).

## Completion criteria
- ADR-014 no longer restates the failure consequence of a not-accepted posture as a fact; it points to ADR-004 for that consequence, while keeping its responsibility-boundary/validation framing.
- `check_adr_structure.py`, `check_adr_preservation.py`, `check_docs_consistency.py --domain agent`, and `check_docs_japanese.py` pass.

## Out of Scope
- Changing ADR-004, ADR-002, ADR-003, ADR-007 (covered by their own rows).
- Adding a distinct subprocess exit status or structured log line (code change out of scope).
- Re-classifying any server as non-required.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-100246 | 20261111-100246 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-100246 | 20261111-100246 | check_adr_structure.py pass; check_adr_preservation.py exit 0 (warnings for ADR-003/007 Decision/Failure-Policy wording; ADR-014 edit is in Tests section, no warning); check_docs_consistency.py --domain agent pass; check_docs_japanese.py pass |

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
- **Requirement ID**: `REQ-004` — stop restating posture handling in ADR-014 and point to ADR-004
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-225014_adrrev007_posture-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-065828
- **Related target files**: `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`