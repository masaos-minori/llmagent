# Fix ADR-006 internal conflicts and remove stale ADR boilerplate

## Priority
Medium

## Summary
ADR-006 contradicts itself, the Index, and ADR-013 in several places, and several ADRs contain copied boilerplate describing an older architecture. Correct both.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-M04`; merged from ADRCHK-M10, L06 (review findings M2, M11, M12, M13, M14 and round 1 Low findings)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified).

## Reason for Change
- ADR-006 conflicts: Manual Review says INV-06 has no automated test while Automated Tests lists one; item 11b says non-empty consumer ID while ADR-013 requires an explicit ID; Alternative B is rejected for blocking out-of-order ACK although the chosen high-water mark model also allows it; `since_seq > 0` overrides the stored offset and can skip unacknowledged events, so At-Least-Once holds only under an unstated condition; the Index says a lower offset is rejected while 11a accepts the ACK and leaves the offset unchanged.
- Boilerplate is stale: ADR-005, ADR-006, and ADR-009 say single DB, re-evaluate when split, although the system uses several databases; ADR-006 says permissions exist only in SQLite, which predates ADR-013; the Out of Scope line about runtime behavior in ADR-001, ADR-002, and ADR-003 does not match their content.

## Implementation Intent
- ADR-006 matches the code in `scripts/eventbus/` and states the exact condition for its delivery guarantee.
- Every sentence in the boilerplate sections describes the current architecture.

## Target Files or Areas
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/10_adr/adr_01_index.md`
- ADR-001, ADR-002, ADR-003, ADR-005, and ADR-009 under `docs/10_adr/`

## Required Changes
- Correct each ADR-006 conflict from the code, and state the `since_seq` condition under the delivery guarantee.
- Make the Index wording for lower offsets match 11a.
- Replace or remove the stale boilerplate sentences.

## Constraints
- If correcting a statement changes the meaning of a decision, for example the delivery guarantee, mark it as a pending amendment.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- Each conflict is resolved, with the evidence (file and symbol) in the PR.
- No ADR contains the single-DB or permissions-only-in-SQLite statements.

## Testing Expectations
Documentation-only. Run the ADR checkers and docs checkers listed in `routing.md`. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. ADR-006 and the other listed ADRs.

## Out of Scope
- Changing EventBus behavior.

## Dependencies
- `issues/20261117-123008_adrchk008_db-data-lifecycle.md` also edits ADR-006 (retention and no-loss wording); fix the order with the owner.
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines the pending-amendment form.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- Mark a meaning-changing correction as a pending amendment; do not write approval text.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123016
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `docs/10_adr/adr_01_index.md`; ADR-001, ADR-002, ADR-003, ADR-005, and ADR-009 under `docs/10_adr/`
