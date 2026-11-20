# Make traceability IDs unique and correct the deviation ledger

## Priority
Medium

## Summary
UNK identifiers collide between documents, the ADR document guide claims no deviations remain, a fixed deviation (SHARED-001) is still listed, and references use hard-coded line numbers. Make IDs unique and the ledger accurate.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H12`; merged from ADRCHK-H16, H20, L13 (review findings H7, N3, N19)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Claims come from the review (`Documentation only` until re-verified). The plans cited as collision sources are archived under `plans/done/`.

## Reason for Change
- UNK IDs collide: UNK-01 means the adrrev002 rotation owner, the adrrev005 sqlite-vec handling, the NACK idempotency key in `scripts/eventbus/ack_route.py`, and a governance_03 item cited by ADR-006 and ADR-013 that does not exist; UNK-03 is also reused. The Known Deviation sync check ignores the `UNK-` prefix, so nothing detects this.
- The guide is wrong: `adr_00_document-guide.md` says no confirmed deviation remains while other deviations are open.
- A fixed deviation is still listed: SHARED-001 is fixed (read-only connections keep the journal mode, covered by `test_run_integrity_check_keeps_rollback_journal_mode`), yet the ledger lists it as open and ADR-008 says Known Deviations is Not applicable while citing SHARED-001.
- References use line numbers (SHARED-002 and a comment in `scripts/shared/tool_constants.py`), which break on any edit and violate `skills/DESIGN.md`.

## Implementation Intent
- Every UNK ID referenced outside its own plan is globally unique and resolves in governance_03, and the sync check enforces this.
- The guide points to the ledger instead of making claims, and the ledger reflects the code.
- References use section names or symbols.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `docs/10_adr/adr_00_document-guide.md`
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
- scripts/eventbus/ack_route.py (comment)
- scripts/agent/services/config_validators.py (comment)
- scripts/shared/tool_constants.py (comment)
- `tools/check_known_deviation_sync.py`
- `tests/tools/`

## Required Changes
- Register the item that ADR-006 and ADR-013 mean in governance_03 with a unique ID, and update both ADRs.
- Replace plan-local IDs in code comments with the global ID or the plan path.
- Extend the sync check to `UNK-` references.
- Run `test_run_integrity_check_keeps_rollback_journal_mode`; close SHARED-001 with its result and remove it from the ADR-008 Known Deviations.
- Replace the guide sentence with a pointer to the ledger.
- Replace the line-number references with section names or symbols.

## Constraints
- Do not renumber IDs inside plan files; change only references from outside the plan.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- Every `UNK-` reference in `docs/10_adr/` and `scripts/` resolves to exactly one governance_03 entry (checker test).
- The Known Deviation sync check passes, and the guide makes no count or absence claim.

## Testing Expectations
Checker tests under `tests/tools/`; run `tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py`, the docs checkers, and the named integrity test. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. governance_03 ledger, ADR guide, ADR-006, ADR-008, ADR-013.

## Out of Scope
- Renumbering IDs inside plan files.
- Changing deviation substance.

## Dependencies
- `issues/20261117-123008_adrchk008_db-data-lifecycle.md` also edits ADR-008 and ADR-006; fix the order with the owner.

## Unresolved Questions
- `tools/check_known_deviation_sync.py` was not reviewed; how it parses IDs is `不明`.

## AI Implementation Instruction
- Do not renumber IDs inside plan files. Change only the references from outside the plan.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123012
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `docs/10_adr/adr_00_document-guide.md`; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; `scripts/eventbus/ack_route.py (comment)`; `scripts/agent/services/config_validators.py (comment)`; `scripts/shared/tool_constants.py (comment)`; `tools/check_known_deviation_sync.py`; `tests/tools/`
