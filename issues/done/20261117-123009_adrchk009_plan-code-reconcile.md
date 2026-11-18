# Reconcile the adrrev002 and adrrev005 plans with the code

## Priority
High

## Summary
Both plans report completed work that the code does not show, and their acceptance criteria conflict about EventBus DDL under `scripts/db/`. Make each plan's status match the evidence.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H09`; merged from ADRCHK-H10, H18 (review findings N37, N46)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Both plans are now archived under `plans/done/`, so editing them needs maintainer confirmation. `build_eventbus_schema_sql` is still defined in `scripts/db/schema_sql.py` and used by `tests/db/test_create_schema.py` (`Explicit in code`, confirmed by `rg`). The Pending Work Item claims come from the review.

## Reason for Change
- adrrev005 marks its early phases Completed while several Work Items are Pending, and its deployment phase depends on two open unknowns. Phase 6 edited ADR-001, ADR-006, and ADR-008 with no approval reference. Running the deployment phase now would block the workflow and EventBus services from starting.
- adrrev002 AC-04 requires no `build_eventbus_schema_sql` under `scripts/db/`, but the function and `_EVENTBUS_SCHEMA_PATH` still exist, and adrrev005 asks that each database's DDL be returned by a function of the same shape. The plans conflict, and EventBus DDL ownership is again split.

## Implementation Intent
- Each plan's status matches the evidence.
- The deployment phase lists its blockers explicitly.
- One rule decides whether `scripts/db/` may expose EventBus DDL, and both plans follow it.

## Target Files or Areas
- `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`
- `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`
- `scripts/db/schema_sql.py`
- `tests/db/test_create_schema.py`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

## Required Changes
- (no decision needed) Run `rg -n "build_eventbus_schema_sql" scripts tools tests` and attach the result.
- (no decision needed) For each Pending Work Item in adrrev005, mark it Completed with evidence, or move its Phase back to In Progress.
- (no decision needed) Add the deployment-phase preconditions: the data lifecycle decision recorded and both open unknowns resolved.
- (no decision needed) Reference the approval records for the Phase 6 ADR edits, or mark them pending.
- (decision) Remove `build_eventbus_schema_sql` and `_EVENTBUS_SCHEMA_PATH` from `scripts/db/schema_sql.py` and update their callers, or amend adrrev002 AC-04.

## Constraints
- Do not run the deployment.
- Editing archived plans needs maintainer confirmation of how archived files are corrected.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- No Phase marked Completed has a Pending Work Item.
- The AC-04 search result matches the plan text, and `uv run python tools/check_db_separation.py` passes.

## Testing Expectations
Run `tools/check_db_separation.py`; if the function is removed, run `tests/db/` and the full validation sequence. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The two plans (status, preconditions, AC-04) and governance_03 if unknown items change.

## Out of Scope
- Executing the deployment phase.
- DDL changes.

## Dependencies
- `issues/20261117-123008_adrchk008_db-data-lifecycle.md` must be decided before the deployment phase can start.
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines approval references for the Phase 6 ADR edits.

## Unresolved Questions
- The memo places the plans under `plans/`; they exist only under `plans/done/`. How to correct archived plans is `不明`.
- The state of the two open unknowns in adrrev005 is `不明` without reading the plan.

## AI Implementation Instruction
- Do not run the deployment.
- Attach `rg` evidence for every status change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123009
- **Related target files**: `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`; `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`; `scripts/db/schema_sql.py`; `tests/db/test_create_schema.py`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
