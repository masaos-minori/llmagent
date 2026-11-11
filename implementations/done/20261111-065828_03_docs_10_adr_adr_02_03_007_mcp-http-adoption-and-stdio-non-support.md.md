## Goal

Stop ADR-007 from restating the posture-abort rule and replace those restatements with one-line pointers to ADR-004, while preserving ADR-007's own HTTP transport and posture-payload framing.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-004 is the single normative authority for how a `FAILED` posture result is handled; ADR-007 must point to it, not restate the abort or the safety/integrity-vs-availability classification.
- The redundant restatements are: Decision Detail #12 (L80, "...A posture `FAILED` result aborts startup."), the Negative Consequences trigger (L224), and the Fail-Open/Degraded Conditions statement (L228, "A posture `FAILED` result is not an availability failure.").
- These restatements are redundant, not contradictory: L228 already frames posture as "not an availability failure" and cites ADR-004, matching ADR-004's safety/integrity classification. The task is consolidation, not contradiction repair.
- Other ADR-007 locations already reference ADR-004 correctly (Target Environment Profile, Degraded condition, related-ADR list); this row touches only the posture-abort restatements.
- The overlap with adrrev009 on `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` does not touch ADR-007; compatible, non-overlapping.

## Design decisions
- Replace only the clause that states the abort/classification rule with a one-line pointer to ADR-004; keep ADR-007's own content about where the posture travels (authenticated `/health`) and how the Agent validates its contract version and shape.
- Keep the availability-failure-of-a-non-mandatory-component explanation in the Fail-Open/Degraded section (distinct operational guidance, already citing ADR-004); only remove the appended "A posture `FAILED` result is not an availability failure" sentence and point it to ADR-004.

## Alternatives considered
- N/A: single-clause replacements; no design space worth recording.

## Implementation
### Target file
`docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`

### Procedure
1. Open ADR-007.
2. In Decision Detail #12, remove the trailing "A posture `FAILED` result aborts startup." and replace with a one-line pointer to ADR-004 for posture-failure handling. Keep the preceding clause about publishing posture on `/health` and validating contract version/shape.
3. In Fail-Open or Degraded Conditions, remove "A posture `FAILED` result is not an availability failure." and point posture classification to ADR-004; keep the non-mandatory availability-failure explanation.
4. Review the Negative Consequences trigger (L224); if it restates the classification, convert the parenthetical to "per ADR-004"; if it is a bare trigger list entry, leave it.
5. Leave all other sections unchanged.

### Method
- Locate Decision Detail #12 in the Decision Details section, the Negative Consequences list, and the Fail-Open or Degraded Conditions list.
- Edit each targeted clause in place; do not renumber Decision Details or reorder lists.
- Match the surrounding voice.

### Details
- Current #12 (L80): "...the Agent validates only that posture's contract version and shape, never the server's configuration file (item 10). A posture `FAILED` result aborts startup."
- Current Fail-Open/Degraded (L228): "...startup continues in a partial-availability state (ADR-004: an availability failure of a non-mandatory component disables it and startup continues in a partial-availability state). A posture `FAILED` result is not an availability failure."
- Current Negative Consequences (L224): "When an MCP server reports a posture check as `FAILED` on `GET /health` (Safety/Integrity, not an availability failure)."

## Compatibility considerations
- N/A: single-ADR wording change; reinforces the ADR-004 pointer already present elsewhere in ADR-007.

## Security considerations
- Prose-only consolidation; the enforced fail-closed behavior is unchanged in code. State intent, not config values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Structural + invariant preservation: `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` against `HEAD`; confirm no invariant, reference, test citation, Known Deviation, or Approval text changed outside the targeted clauses.
- Cross-domain claim consistency: `uv run python tools/check_docs_consistency.py --domain mcp`.
- Japanese-text policy: `uv run python tools/check_docs_japanese.py` (English only).

## Completion criteria
- ADR-007 no longer restates the posture-abort or posture-classification rule; it points to ADR-004 instead, while keeping its HTTP/posture-payload framing.
- `check_adr_structure.py`, `check_adr_preservation.py`, `check_docs_consistency.py --domain mcp`, and `check_docs_japanese.py` pass.

## Out of Scope
- Changing ADR-004, ADR-002, ADR-003, ADR-014 (covered by their own rows).
- Adding a distinct subprocess exit status or structured log line (code change out of scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-100046 | 20261111-100046 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-100046 | 20261111-100046 | check_adr_structure.py pass; check_adr_preservation.py exit 0 (warnings: ADR-007 Decision #12 + Fail-Open/Degraded + Negative-Consequences wording, mapped in commit); check_docs_consistency.py --domain mcp pass; check_docs_japanese.py pass |

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
- **Requirement ID**: `REQ-003` — stop restating posture handling in ADR-007 and point to ADR-004
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-225014_adrrev007_posture-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-065828
- **Related target files**: `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`