## Goal

Restate ADR-003 Decision Detail #16 so that a server whose Security Posture is "not accepted" is treated identically to a `FAILED` posture result under ADR-004: the server is excluded from `RuntimeToolRegistry`, and because a posture failure is a safety/integrity failure it aborts Agent startup regardless of the server's `required` value.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-004 is the single normative authority for posture handling. A `FAILED` posture is a safety/integrity failure (Group 2 item 5) that aborts startup even when `required = false` (ADR-004 decision text); ADR-003 must point to this, not redefine it.
- The current ADR-003 Decision Detail #16 frames the exclusion purely as a static-availability computation and does not mention the `required = false` abort, so a reader can downgrade a safety failure to an availability warning.
- This row does not overlap with adrrev009: adrrev007 edits ADR-003 here; adrrev009 edits `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`. Non-overlapping sections; compatible, both land without contradiction.
- The edit stays within the single Decision Detail #16 body; all other ADR-003 text (invariants, approval, related-ADR links) stays byte-identical.

## Design decisions
- Keep the existing registry-exclusion framing ("excluded when `RuntimeToolRegistry` is constructed") and append the ADR-004 abort consequence, rather than replacing #16 with an ADR-004 restatement: ADR-003 owns the registry-construction decision, ADR-004 owns the failure-handling consequence.
- Equate "not accepted" with `FAILED` explicitly for this rule so the two phrases cannot drift.

## Alternatives considered
- N/A: single-clause wording fix; no design space worth recording.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
1. Open ADR-003 and locate Decision Detail #16 under "### Decision Details".
2. Rewrite the single paragraph so it states both (a) a server whose posture is not accepted is excluded from `RuntimeToolRegistry` (Tools neither exposed to the LLM nor routable), and (b) a `FAILED` posture aborts Agent startup regardless of `required`, and that "not accepted" means the same as `FAILED` for this rule.
3. Leave every other section of ADR-003 unchanged.

### Method
- Locate Decision Detail #16 in the Decision Details section.
- Edit the single paragraph in place; do not move or renumber adjacent Decision Details.
- Match the surrounding voice: present-tense, imperative policy statements.

### Details
- Current #16 reads: "A server whose Security Posture is not accepted is excluded when `RuntimeToolRegistry` is constructed, so its Tools are neither exposed to the LLM nor routable. The exclusion is a Static Availability decision (Decision Detail #11): it is computed once at startup from the posture each server publishes on its own `/health`, it is not a Dynamic Health state, and it is not re-evaluated until the process restarts (Decision Detail #14)." It omits the ADR-004 mandate that a `FAILED` posture aborts startup regardless of `required`.
- The added clause must not reintroduce an availability-failure carve-out: ADR-004 item 8 (partial availability) does not apply to posture failures, and Group 7 items 18-19 (non-mandatory disable) are inapplicable while every server is `required`.
- Do not copy ADR-004's exit-status or config values into ADR-003; reference the authority by name.
- Preserve the existing cross-references to ADR-004 in ADR-003's related-ADR and review-trigger text.

## Compatibility considerations
- N/A: single-ADR wording change; reinforces the ADR-004 pointer already present in ADR-002/007/014.

## Security considerations
- Prose-only hardening of a safety property; the enforced fail-closed behavior is unchanged in code, so the security boundary is identical. State intent, not config values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Structural + invariant preservation: `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_preservation.py` against `HEAD`; confirm no invariant, reference, test citation, Known Deviation, or Approval text changed outside the single clause.
- Cross-domain claim consistency: `uv run python tools/check_docs_consistency.py --domain mcp`.
- Japanese-text policy: `uv run python tools/check_docs_japanese.py` (English only).

## Completion criteria
- Decision Detail #16 states that a "not accepted" posture is excluded from `RuntimeToolRegistry` and that a `FAILED` posture aborts Agent startup regardless of `required`, with "not accepted" defined as `FAILED` for this rule.
- `check_adr_structure.py`, `check_adr_preservation.py`, `check_docs_consistency.py --domain mcp`, and `check_docs_japanese.py` pass.

## Out of Scope
- Changing ADR-004, ADR-002, ADR-007, ADR-014 (covered by their own rows).
- Adding a distinct subprocess exit status or structured log line (code change out of scope).
- Re-classifying any server as non-required.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-095759 | 20261111-095759 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-095759 | 20261111-095759 | check_adr_structure.py pass; check_adr_preservation.py exit 0 (warning: Decision #16 wording change, mapped in commit); check_docs_consistency.py --domain mcp pass; check_docs_japanese.py pass |

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
- **Requirement ID**: `REQ-001` — equate "not accepted" with `FAILED` and state the `required`-independent startup abort in ADR-003 Decision Detail #16
- **Source issue**: `issues/20261109-112814_adrrev007_posture-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-225014_adrrev007_posture-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-065828
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`