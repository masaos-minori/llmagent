# Implementation Procedure: Remove AGENT-003 from ADR-004 Known Deviations

## Goal

Remove AGENT-003 from the Known Deviations section of ADR-004, completing the resolution of the Orchestrator fallback mode issue.

## Scope

- Remove AGENT-003 reference from `docs/10_adr/ADR-004-environment-failure-handling-policy.md` Known Deviations section.

## Assumptions

- AGENT-003 is fully resolved by the companion implementation procedure for `scripts/agent/orchestrator.py` (removing fallback mode).
- No other issues reference AGENT-003 as a dependency.

## Design decisions

Remove the AGENT-003 line from the Known Deviations section. This is a straightforward deletion — no restructuring needed since AGENT-003 is the only item being removed from this section.

## Alternatives considered

- **Mark AGENT-003 as "resolved" instead of removing**: Would leave a historical record but clutter the Known Deviations section with resolved items. Removal is cleaner per the repository's convention of removing resolved items.

## Implementation steps

1. Remove AGENT-003 reference from `docs/10_adr/ADR-004-environment-failure-handling-policy.md` Known Deviations section.
   - Find the line `- **Known Issue**: AGENT-003 — tracked in governance_03 Part 1 (Orchestrator fallback mode when the workflow fails to load)`.
   - Remove this line.

## Acceptance criteria

- AGENT-003 is removed from ADR-004 Known Deviations.

## Tests

- Manual verification: `rg "AGENT-003" docs/10_adr/ADR-004-environment-failure-handling-policy.md` returns zero matches.

## Documentation Impact

This procedure updates a documentation file only — no source code changes.

## Risks

- **Risk**: Other issues may reference AGENT-003 as a dependency → **Mitigation**: Check for cross-references before removal.

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-150310_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261008-150310
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md

### Requirement Traceability

| Requirement ID | Source Issue Section or Evidence | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-005 | Documentation Impact: remove AGENT-003 from ledger and ADR Known Deviations | docs/10_adr/ADR-004-environment-failure-handling-policy.md | Step 1 | AGENT-003 removed from ADR Known Deviations | rg AGENT-003 | Confirmed by repository evidence |
