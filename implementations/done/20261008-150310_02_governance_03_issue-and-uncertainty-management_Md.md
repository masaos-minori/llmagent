# Implementation Procedure: Remove AGENT-003 from governance tracker

## Goal

Remove AGENT-003 from the Known Issues ledger and ADR Known Deviations, completing the resolution of the Orchestrator fallback mode issue.

## Scope

- Remove AGENT-003 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 (Known Issues table).
- Remove AGENT-003 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 2 (Known Issues detailed section).
- Remove AGENT-003 reference from `docs/10_adr/ADR-001-workflow-engine-mandatory.md` Known Deviations section.
- Remove AGENT-003 reference from `docs/10_adr/ADR-004-environment-failure-handling-policy.md` Known Deviations section.

## Assumptions

- AGENT-003 is fully resolved by the companion implementation procedure for `scripts/agent/orchestrator.py` (removing fallback mode).
- No other issues reference AGENT-003 as a dependency.

## Design decisions

Remove AGENT-003 entries from all four locations where it appears. This is a straightforward deletion — no restructuring needed since AGENT-003 is the only item being removed from these sections.

## Alternatives considered

- **Mark AGENT-003 as "resolved" instead of removing**: Would leave a historical record but clutter the Known Issues ledger with resolved items. Removal is cleaner per the repository's convention of removing resolved items.

## Implementation steps

1. Remove AGENT-003 from the Known Issues table in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1.
   - Find the row containing `AGENT-003` and remove it.
   - Verify no other rows need renumbering.

2. Remove AGENT-003 from the Known Issues detailed section in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 2.
   - Find the `#### AGENT-003` heading and its associated bullet points.
   - Remove the entire section.

3. Remove AGENT-003 reference from `docs/10_adr/ADR-001-workflow-engine-mandatory.md` Known Deviations section.
   - Find the line `- **Known Issue**: AGENT-003 — tracked in governance_03 Part 1 (Orchestrator fallback mode when the workflow fails to load)`.
   - Remove this line.

4. Remove AGENT-003 reference from `docs/10_adr/ADR-004-environment-failure-handling-policy.md` Known Deviations section.
   - Find the line `- **Known Issue**: AGENT-003 — tracked in governance_03 Part 1 (Orchestrator fallback mode when the workflow fails to load)`.
   - Remove this line.

## Acceptance criteria

- AGENT-003 is removed from the Known Issues ledger and ADR Known Deviations.

## Tests

- Manual verification: `rg "AGENT-003"` returns zero matches across all four files.

## Documentation Impact

This procedure updates documentation files only — no source code changes.

## Risks

- **Risk**: Other issues may reference AGENT-003 as a dependency → **Mitigation**: Check for cross-references before removal.

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-150310_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261008-150310
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md, docs/10_adr/ADR-001-workflow-engine-mandatory.md, docs/10_adr/ADR-004-environment-failure-handling-policy.md

### Requirement Traceability

| Requirement ID | Source Issue Section or Evidence | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-005 | Documentation Impact: remove AGENT-003 from ledger and ADR Known Deviations | docs/00_governance/governance_03_issue-and-uncertainty-management.md, docs/10_adr/ADR-001-workflow-engine-mandatory.md, docs/10_adr/ADR-004-environment-failure-handling-policy.md | Step 1-4 | AGENT-003 removed from all three docs | rg AGENT-003 | Confirmed by repository evidence |
