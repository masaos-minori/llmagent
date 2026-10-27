# Reconcile the EVENTBUS-019 to EVENTBUS-023 Known Issue entries with the implemented fixes

## Priority
High

## Summary
The Known Issue ledger and the ADR `Known Deviations` sections still list EVENTBUS-019 to EVENTBUS-023 as open High issues, although the related implementation work has been merged. Verify each entry's Resolution Target against the current source and tests, then remove the entries that are resolved from the ledger and from the ADRs in the same change, and keep the entries that are not.

## Background
- `governance_03_issue-and-uncertainty-management.md` Part 1 lists EVENTBUS-019 to EVENTBUS-023 with `Status: open` and `Severity: High`. Evidence: `Explicit in code` (document text).
- `governance_03` states that an item is removed from the active inventory once it is resolved. Evidence: `Explicit in code` (document text).
- `governance_01_documentation-policy.md` Merge Conditions list "High-severity open Known Issue exists in affected area" as a Blocking Condition. Stale open High entries therefore block merges in the EventBus area. Evidence: `Explicit in code` (document text).
- Implementation commits exist for each entry: DLQ requeue atomicity (`39335dc89`), startup fingerprint gate and deployment readiness (`72c83c0db`), fail-fast shutdown (`e5f30fefe`), NACK idempotency key and "close EVENTBUS-023" (`dbbd4357d`), and later test alignment (`57ed943ff`). Evidence: `Operationally observed` (git log). For EVENTBUS-020 (config loader and duplicate tokens) no commit was identified by message; the current loader passes both mappings and the duplicate-token guard exists in the auth module. Evidence: `Strongly implied by code`.
- `check_known_deviation_sync.py` currently reports one warning: EVENTBUS-023 targets ADR-006 but ADR-006 `Known Deviations` does not cite it. Commit `dbbd4357d` removed the ADR citation without removing the ledger entry. Evidence: `Verified by test` (tool run).
- ADR-006 `Known Deviations` still cites EVENTBUS-019, EVENTBUS-021 and EVENTBUS-022. ADR-004 cites EVENTBUS-021. ADR-013 cites EVENTBUS-020. Evidence: `Explicit in code`.
- The Execution Status tables of the archived plans for the DLQ requeue, config loader and NACK issues (`plans/done/20261025-095644_eventbus001_dlq-requeue-transactional.md`, `plans/done/20261025-101136_eventbus002_config-authorization-token-roles.md`, `plans/done/20261025-120857_eventbus005_nack-idempotency-retries.md`) still show `In Progress`, while the startup-gate and shutdown plans show `Completed`. Evidence: `Explicit in code`; this is a separate record drift and does not decide whether the ledger entries are resolved.
- No open issue or in-flight plan under `issues/` or `plans/` overlaps this ledger work.

## Problem
Ledger entries that describe fixed defects remain open. They block merges in the EventBus area under the Merge Conditions, the ledger and the ADR sections disagree for EVENTBUS-023, and readers are told that defects exist which the code no longer has. Conversely, removing an entry without checking its Resolution Target could hide a defect that is still present.

## Reason for Change
The stale High entries gate merges now, and the sync checker already reports the EVENTBUS-023 inconsistency. The ledger is meant to be the single place for active design-versus-code discrepancies, so an inaccurate entry defeats its purpose.

## Implementation Intent
Treat each entry's `Resolution Target` as the acceptance test. For each of the five entries, verify against the current source and tests whether the target is met, using the entry's own wording (atomic requeue with no SQLite access in the route and negative/concurrency tests; mapping reaches the Consumer principal and duplicate tokens are rejected at load; stamped-but-malformed database rejected by both paths and readiness verified before reporting started; connection never closed while another worker may use it; retry of the same delivery attempt not counted again with an identical contract in API, documents and tests). Remove a resolved entry from the ledger and from every `Known Deviations` section that cites it in one change. Keep an unresolved entry and update its `Observed Implementation` to the current state. Do not change code or tests in this issue.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1 Active Items)
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` (`Known Deviations`)
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (`Known Deviations`)
- `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` (`Known Deviations`)
- `docs/10_adr/adr_00_document-guide.md` (sentence listing confirmed deviations)
- Read-only evidence: `scripts/eventbus/`, `scripts/shared/eventbus_schema_fingerprint.py`, `scripts/db/create_schema.py`, `deploy/init_db.sh`, `deploy/setup_services.sh`, `tests/eventbus/`, `tests/db/`, `tests/deploy/`

## Required Changes
- For each of EVENTBUS-019 to EVENTBUS-023, record the verification of the Resolution Target (source and test evidence, or the unmet part).
- Remove each resolved entry from `governance_03` Part 1 and from each ADR `Known Deviations` that cites it, in the same change.
- Update an unresolved entry's current-state fields instead of removing it.
- Update the `adr_00_document-guide.md` sentence so it lists only deviations that remain, or states that none remain.
- Run the sync checker and clear the EVENTBUS-023 warning.

## Constraints
- A Known Issue MUST NOT be removed on the basis of documentation or commit messages alone; each removal requires source and test evidence for the Resolution Target (`skills/DESIGN.md` Evidence labels).
- The ledger entry and every ADR citation MUST be removed together (`check_known_deviation_sync.py` is bidirectional).
- `docs/` content MUST be English and MUST follow `skills/DESIGN.md` "Docs content policy — remove" (no source line numbers).
- ADR Decisions, Invariants and Approval records MUST NOT change; `check_adr_preservation.py` MUST report no ERROR other than the intended Known Deviations changes.

## Acceptance Criteria
- Every one of the five entries is either removed (with recorded source and test evidence for its Resolution Target) or retained with its current-state fields updated.
- No ledger entry exists without a matching ADR `Known Deviations` citation, and no citation exists without a ledger entry.
- `uv run python tools/check_known_deviation_sync.py` reports no warning.
- `adr_00_document-guide.md` lists exactly the deviations that remain.
- The checkers listed under Testing Expectations pass.

## Testing Expectations
Documentation-only change (evidence gathering may run existing tests read-only). Run:
- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/check_adr_structure.py`
- `uv run python tools/check_adr_preservation.py` (review the Known Deviations changes)
- `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py` on the changed files
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_consistency.py --domain eventbus`
- `uv run python tools/check_docs_japanese.py`
- `uv run pytest tests/eventbus tests/db -q` to confirm the cited tests pass.

## Documentation Impact
`governance_03` and the affected ADRs must be updated: kind of information is Known Issues (active register and Known Deviations). If an entry is retained, its Observed Implementation and Resolution Target state must reflect the current behavior.

## Out of Scope
- Any change to `scripts/`, `deploy/` or `tests/`.
- Registering EventBus issues 006 to 008 or any new Known Issue.
- Correcting the stale Execution Status tables of the archived plans.
- Resolving the CI state of the repository.

## Dependencies
N/A: none. No open issue or in-flight plan overlaps. This issue is independent of the other issues in this batch.

## Unresolved Questions
- Is each Resolution Target fully met? `Needs confirmation` per entry. EVENTBUS-020 in particular has no identified implementing commit, and the archived plan tables for 019, 020 and 023 still show `In Progress`.
- Does the "CI Evidence" expectation used when these entries were registered apply, given that CI on the main branch was recorded as failing for a runner reason unrelated to EventBus (recorded 2026-10-25, current state `不明`)? `Needs confirmation`.
- Who is the accountable approver for removing High Known Issues? `不明`; Owner is currently `Repository owner`.

## AI Implementation Instruction
Do not modify source code or tests. Verify each entry against the current source before removing it, and cite the evidence in the change description. Remove ledger entries and ADR citations together. If any Resolution Target is not met, keep the entry and report which part is unmet. Write in English. Stop and report if `check_known_deviation_sync.py` shows a new inconsistency after the change.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-102048
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_00_document-guide.md`
