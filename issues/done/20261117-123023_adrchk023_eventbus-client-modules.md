# Decide the fate of unused EventBus client modules

## Priority
Low

## Summary
`scripts/agent/eventbus_subscriber.py` and `scripts/agent/eventbus_topic_admin_client.py` are imported only by their tests, and governance requires a recorded decision.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-L02`; merged from ADRCHK-L21 (round 2 Low finding, adrrev002 UNK-02)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
The modules appear in the generated API reference but no production code uses them (`Documentation only` until confirmed with `rg`).

## Reason for Change
- The modules look like a supported API.
- Under the governance_03 Unused Features rule, unused code must be either registered as a design gap or removed, and adrrev002 UNK-02 left this undecided.

## Implementation Intent
- The decision is recorded, and the code and the reference match it.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md (path now under done/)

## Required Changes
- (decision) Register a design-gap entry, or file a removal plan.

## Constraints
- Do not delete the modules in this issue.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- governance_03 records the decision, and the adrrev002 UNK-02 text refers to it.

## Testing Expectations
Not required (documentation-only). Run the docs checkers and `tools/check_needs_confirmation_inventory.py`. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. governance_03: the design-gap entry or removal reference.

## Out of Scope
- Deleting the modules.
- EventBus behavior changes.

## Dependencies
- `issues/20261117-123009_adrchk009_plan-code-reconcile.md` reconciles the same plan; fix the order with the owner.

## Unresolved Questions
- Whether archived plans may be edited is `不明`; the plan is under `plans/done/`.

## AI Implementation Instruction
- Do not delete the modules in this package.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123023
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md (path now under done/)`
